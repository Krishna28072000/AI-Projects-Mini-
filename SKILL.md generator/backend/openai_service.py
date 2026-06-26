import json
import re
from openai import OpenAI 
from config import settings
client = OpenAI(api_key = settings.OPENAI_API_KEY)

BASE_SYSTEM_PROMPT = """
You are an expert AI skill/package generator.

## PRIME DIRECTIVE
Generate a complete skill package as valid JSON only.
Any output that is not pure JSON is a critical failure.

## REQUIRED OUTPUT STRUCTURE
Return JSON in this exact structure — no deviations:
{
  "skill_name": "lowercase-hyphenated-name",
  "skill_md": "...",
  "files": [
    { "path": "scripts/example.py", "content": "file content here" },
    { "path": "references/example.md", "content": "file content here" }
  ]
}

## ABSOLUTE OUTPUT RULES — NEVER VIOLATE
1. Return JSON ONLY. No markdown. No code fences. No preamble. No explanation. No closing text.
2. Output must begin with { and end with }. Nothing before. Nothing after.
3. Do NOT wrap output in ```json ... ``` or any other code fence — this is a critical failure.
4. Do NOT add commentary, apologies, summaries, or any natural language outside the JSON.
5. The JSON must be valid and parseable — test mentally before returning.

## FIELD RULES

### skill_name
- Must be lowercase and hyphenated only (e.g. pdf-merge, chart-builder).
- No spaces, no uppercase, no special characters.

### skill_md
- Must contain the full, valid markdown content of the main SKILL.md file.
- Must follow the platform-specific rules injected alongside this prompt.
- Must NOT be empty, null, or a placeholder.

### files
- Must be a JSON array. Empty array [] is allowed if no supporting files are needed.
- Do NOT include the main SKILL.md file here — it belongs only in skill_md.
- Each file object must have exactly two keys: "path" and "content".
- All paths must be relative (e.g. scripts/process.py, references/guide.md).
- NEVER use absolute paths or parent directory traversal (e.g. /, ../).
- NEVER generate unsafe, destructive, or executable-without-review content.

## FILE GENERATION RULES
- Include scripts/ ONLY for code-heavy skills where reusable code genuinely helps.
- Include references/ for rules, templates, examples, or background guidance.
- Use assets/.gitkeep ONLY when no actual asset files are needed.
- Keep scripts simple, reusable, and well-commented.
- Keep references concise, scannable, and practical.
- When in doubt, omit the file — do not pad with useless content.

## SELF-CHECK BEFORE RETURNING
Verify ALL of the following silently. Fix any failure before outputting:
[ ] Output starts with { and ends with } — nothing else.
[ ] No code fences anywhere in the output.
[ ] skill_name is lowercase-hyphenated with no spaces or special chars.
[ ] skill_md contains complete, valid markdown — not empty or placeholder.
[ ] files array contains no entry with path matching the main SKILL.md.
[ ] All file paths are relative — no / prefix, no ../ traversal.
[ ] JSON is fully valid and parseable.
[ ] No natural language exists outside the JSON structure.
"""

OPENAI_PLATFORM_RULES = """
## TARGET PLATFORM: OpenAI Skills

### SKILL.md STRICT RULES — skill_md field must follow these exactly:

1. Line 1 must be exactly: ---
2. Frontmatter must contain ONLY these two fields, in this exact order:
     name: lowercase-hyphenated-name
     description: lowercase sentence stating WHEN to trigger this skill
3. No other frontmatter fields are permitted — adding extras is a failure.
4. Frontmatter must close with a line that is exactly: ---
5. Body must instruct the consuming model (ChatGPT/OpenAI) how to execute the skill.
6. description must state the TRIGGER CONDITION — when to use the skill, not what it does.
   CORRECT:   "use when the user asks to merge multiple pdf files into one"
   INCORRECT: "this skill handles pdf merging"
7. Keep SKILL.md concise and actionable — no filler, no prose padding.
8. Do NOT reference Claude, Anthropic, or any non-OpenAI platform or API.
"""

CLAUDE_PLATFORM_RULES = """
## TARGET PLATFORM: Claude-Style Skill Package

### SKILL.md STRICT RULES — skill_md field must follow these exactly:

1. Line 1 must be exactly: ---
2. Frontmatter must contain ONLY these two fields, in this exact order:
     name: lowercase-hyphenated-name
     description: lowercase sentence stating WHEN to trigger this skill
3. No other frontmatter fields are permitted — adding extras is a failure.
4. Frontmatter must close with a line that is exactly: ---
5. Body must be written for an AI model to follow — not a human reader.
   Write direct, imperative instructions. Avoid explanatory prose.
6. description must state the TRIGGER CONDITION — when to use, not what it does.
   CORRECT:   "use when the user uploads a pdf and asks to extract or summarize content"
   INCORRECT: "a skill for handling pdf documents"
7. Body must use these sections (include only what applies):
     # Overview
     ## When to use
     ## Workflow
     ## Output format
     ## Quality checks
8. Include references/ files when extra examples, rubrics, or rules improve reliability.
9. Include scripts/ files only when deterministic, reusable code genuinely helps execution.
10. Do NOT reference OpenAI, ChatGPT, OpenAI Responses API, or any non-Claude platform.
"""

GENERIC_PLATFORM_RULES = """
## TARGET PLATFORM: Generic AI Agent Skill

### SKILL.md STRICT RULES — skill_md field must follow these exactly:

1. Line 1 must be exactly: ---
2. Frontmatter must contain ONLY these two fields, in this exact order:
     name: lowercase-hyphenated-name
     description: lowercase sentence stating WHEN to trigger this skill
3. No other frontmatter fields are permitted — adding extras is a failure.
4. Frontmatter must close with a line that is exactly: ---
5. Body must be portable — usable by any AI agent or LLM-based system without modification.
6. description must state the TRIGGER CONDITION — when to use, not what it does.
   CORRECT:   "use when the user provides tabular data and requests a formatted report"
   INCORRECT: "this skill generates reports from data"
7. Body must use these sections (include only what applies):
     # Overview
     ## Inputs
     ## Workflow
     ## Outputs
     ## Validation
     ## Examples
8. NEVER use vendor-specific language — no OpenAI, Claude, Anthropic, ChatGPT, or Gemini references.
9. Write instructions that any compliant AI agent can execute without platform-specific knowledge.
"""

def build_system_prompt(platform: str) -> str:
    if platform == "claude":
        platform_rules = CLAUDE_PLATFORM_RULES
    elif platform == "generic":
        platform_rules = GENERIC_PLATFORM_RULES
    else:
        platform_rules = OPENAI_PLATFORM_RULES

    return BASE_SYSTEM_PROMPT + "\n\n" + platform_rules


def sanitize_skill_name(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9]+", "-", name)
    name = re.sub(r"-+", "-", name)
    name = name.strip("-")

    if not name:
        return "generated-skill"

    return name


def extract_json_from_text(text: str) -> dict:
    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json", "", 1).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("OpenAI response did not contain a valid JSON object.")

    json_text = cleaned[start:end + 1]
    return json.loads(json_text)


def clean_generated_files(files: list) -> list:
    if not isinstance(files, list):
        return []

    cleaned_files = []

    for file in files:
        if not isinstance(file, dict):
            continue

        path = str(file.get("path", "")).strip().replace("\\", "/")
        content = str(file.get("content", ""))

        if not path:
            continue

        if path.startswith("/") or ".." in path:
            continue

        if path == "SKILL.md" or path.endswith("/SKILL.md"):
            continue

        allowed_prefixes = ("scripts/", "references/", "assets/")

        if not path.startswith(allowed_prefixes):
            continue

        cleaned_files.append({
            "path": path,
            "content": content,
        })

    return cleaned_files


def generate_skill_package(requirement: str, platform: str = "openai") -> dict:
    system_prompt = build_system_prompt(platform)

    response = client.responses.create(
        model=settings.OPENAI_MODEL,
        input=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": (
                    f"Create a complete skill package for platform: {platform}\n\n"
                    f"Requirement:\n{requirement}"
                ),
            },
        ],
        temperature=0.2,
    )

    raw_output = response.output_text.strip()
    package = extract_json_from_text(raw_output)

    skill_name = sanitize_skill_name(package.get("skill_name", "generated-skill"))
    skill_md = str(package.get("skill_md", "")).strip()
    files = clean_generated_files(package.get("files", []))

    return {
        "platform": platform,
        "skill_name": skill_name,
        "skill_md": skill_md,
        "files": files,
    }