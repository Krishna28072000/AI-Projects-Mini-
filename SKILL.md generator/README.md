# Multi-Platform Skill Generator

A FastAPI-based web application that generates AI skill packages from a user requirement.
The application supports generating skill markdown and downloadable ZIP packages for multiple target platforms such as OpenAI, Claude, and generic AI agents.

## Features

* Generate skill markdown from a plain-language requirement.
* Select target platform:

  * OpenAI Skill
  * Claude Skill
  * Generic AI Agent Skill
* Generate supporting files automatically when useful.
* Validate generated skill markdown.
* Preview generated package structure.
* Copy generated markdown.
* Download generated `SKILL.md`.
* Download full skill package as a ZIP file.
* Serve frontend directly from FastAPI.
* Run the full app using `python main.py`.

## Project Structure

```text
skill_md_generator/
│
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── schemas.py
│   ├── openai_service.py
│   ├── skill_validator.py
│   ├── zip_service.py
│   ├── requirements.txt
│   └── .env
│
└── frontend/
    ├── index.html
    ├── style.css
    └── script.js
```

## Generated ZIP Structure

Example output:

```text
data-visualizer-openai.zip
└── data-visualizer/
    ├── SKILL.md
    ├── scripts/
    │   └── create_chart.py
    ├── references/
    │   └── chart-selection-rules.md
    └── assets/
        └── .gitkeep
```

## Supported Platforms

### OpenAI Skill

Generates an OpenAI-style `SKILL.md` file with YAML frontmatter:

```markdown
---
name: data-visualizer
description: use this skill when the user asks to generate charts or visual summaries from csv data.
---
```

### Claude Skill

Generates Claude-oriented skill instructions with reusable workflow sections and optional reference files.

### Generic AI Agent Skill

Generates portable skill instructions that can be reused with different AI agents.

## Requirements

* Python 3.10+
* OpenAI API key
* FastAPI
* Uvicorn
* OpenAI Python SDK
* python-dotenv
* Pydantic

## Installation

### 1. Clone or create the project folder

```bash
cd "skill_md_generator"
```

### 2. Create virtual environment

```bash
python -m venv venv
```

### 3. Activate virtual environment

For Windows:

```bash
venv\Scripts\activate
```

For macOS/Linux:

```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

## Environment Setup

Create a `.env` file inside the `backend` folder:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4.1-mini or your model preference
```

Do not hardcode your API key inside Python files.

## Run the Application

From the `backend` folder:

```bash
python main.py
```

Open the app in browser:

```text
http://127.0.0.1:8000
```

API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## How to Use

1. Open the local URL in your browser.
2. Select the target platform:

   * OpenAI Skill
   * Claude Skill
   * Generic AI Agent Skill
3. Enter your skill requirement.

Example:

```text
Create a skill that generates data visualizations from CSV files using Python and Plotly. It should inspect columns, choose chart type, write reusable plotting code, save the chart as HTML, and return a short summary.
```

4. Click **Generate Skill Package**.
5. Review the generated markdown.
6. Check the validation result.
7. Preview the package structure.
8. Download:

   * `SKILL.md`
   * Full Skill ZIP

## API Endpoints

### `GET /`

Serves the frontend application.

### `POST /generate-skill-md`

Generates skill markdown and supporting files.

Request body:

```json
{
  "platform": "openai",
  "requirement": "Create a skill that reviews FastAPI code and suggests clean architecture improvements."
}
```

Response:

```json
{
  "platform": "openai",
  "skill_name": "fastapi-code-review",
  "skill_md": "---\nname: fastapi-code-review\n...",
  "files": [
    {
      "path": "references/security-checklist.md",
      "content": "# Security Checklist\n..."
    }
  ],
  "validation": {
    "is_valid": true,
    "errors": []
  }
}
```

### `POST /download-skill-zip`

Creates and downloads the full skill ZIP package.

Request body:

```json
{
  "platform": "openai",
  "skill_name": "fastapi-code-review",
  "skill_md": "---\nname: fastapi-code-review\n...",
  "files": [
    {
      "path": "references/security-checklist.md",
      "content": "# Security Checklist\n..."
    }
  ]
}
```

Response:

```text
application/zip
```

## Validation Rules

The app validates generated skill markdown before ZIP download.

Validation checks include:

* Markdown starts with YAML frontmatter.
* Frontmatter starts and ends with `---`.
* `name` field exists.
* `description` field exists.
* Skill name is lowercase and hyphenated.
* Only `name` and `description` are allowed in frontmatter.
* Body contains useful instructions.

## Important Notes

* OpenAI mode is designed for OpenAI-style Skills.
* Claude mode is Claude-oriented but may need adjustment based on Claude’s exact current upload requirements.
* Generic mode is platform-neutral.
* The generated ZIP should be reviewed before production use.
* API keys must be kept private and should never be committed to Git.

## Example Requirements

### Data Visualization Skill

```text
Create a skill that generates data visualizations from CSV files using Python and Plotly. It should inspect columns, choose chart type, write reusable plotting code, save the chart as HTML, and return a short summary.
```

### FastAPI Review Skill

```text
Create a reusable skill that reviews FastAPI code, checks folder structure, finds security issues, and suggests clean architecture improvements.
```

### Meeting Notes Skill

```text
Create a skill that converts rough meeting notes into professional minutes of meeting with decisions, risks, owners, and action items.
```

## Future Enhancements

Planned improvements:

* Add edit mode for generated markdown.
* Add platform-specific validation for Claude and OpenAI.
* Generate `Skill.md` instead of `SKILL.md` for Claude mode if needed.
* Add direct upload to OpenAI Skills API.
* Add ZIP upload validation.
* Add history of generated skills.
* Add template presets for common skill types.
* Add authentication for safe API key usage.
* Add deployment support.

## Troubleshooting

### App shows “Something went wrong”

Check the backend terminal for the real Python error.

Common causes:

* Missing API key in `.env`.
* Invalid OpenAI model name.
* JSON parsing error from model output.
* Backend not restarted after code changes.
* Frontend JavaScript cache issue.

### Frontend not loading

Make sure this structure exists:

```text
skill_md_generator/
├── backend/
└── frontend/
```

Then run:

```bash
cd backend
python main.py
```

Open:

```text
http://127.0.0.1:8000
```

### ZIP download not working

Check if the generated markdown is valid. ZIP download is blocked when validation fails.

## License

This project is for learning and internal development. Add your preferred license before publishing publicly.
