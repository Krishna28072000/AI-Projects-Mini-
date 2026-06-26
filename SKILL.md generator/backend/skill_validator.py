import re


def validate_skill_md(skill_md: str) -> dict:
    errors = []

    if not skill_md or not skill_md.strip():
        return {
            "is_valid": False,
            "errors": ["Skill markdown content is empty."]
        }

    content = skill_md.strip()

    if not content.startswith("---"):
        errors.append("Markdown file must start with YAML frontmatter using ---.")

    lines = content.splitlines()

    if len(lines) < 4:
        errors.append("Markdown content is too short.")
        return {
            "is_valid": False,
            "errors": errors
        }

    closing_index = None

    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            closing_index = index
            break

    if closing_index is None:
        errors.append("YAML frontmatter must close with ---.")
        return {
            "is_valid": False,
            "errors": errors
        }

    frontmatter_lines = lines[1:closing_index]
    body_lines = lines[closing_index + 1:]

    body = "\n".join(body_lines).strip()

    name = None
    description = None

    for line in frontmatter_lines:
        stripped = line.strip()

        if stripped.startswith("name:"):
            name = stripped.replace("name:", "", 1).strip()

        if stripped.startswith("description:"):
            description = stripped.replace("description:", "", 1).strip()

    if not name:
        errors.append("Frontmatter must include a non-empty name field.")

    if not description:
        errors.append("Frontmatter must include a non-empty description field.")

    if name:
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name):
            errors.append("Skill name must be lowercase, hyphenated, and contain only letters, numbers, and hyphens.")

    if description:
        if len(description) < 30:
            errors.append("Description should be more specific and at least 30 characters long.")

    allowed_keys = {"name", "description"}

    for line in frontmatter_lines:
        if ":" in line:
            key = line.split(":", 1)[0].strip()
            if key not in allowed_keys:
                errors.append(f"Unsupported frontmatter key found: {key}. Only name and description are allowed.")

    if not body:
        errors.append("Markdown file must contain instruction content after the frontmatter.")

    if body and len(body.split()) < 25:
        errors.append("Body should contain more detailed instructions.")

    return {
        "is_valid": len(errors) == 0,
        "errors": errors
    }