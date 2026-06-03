# AI-Powered Resume Shortlisting & Recruitment Automation Tool

An MVP recruitment platform that ingests bulk resumes, parses them with OpenAI, and ranks candidates against a job description using embedding-based semantic matching.

Built per your requirement specification — see `docs/SPEC.md` for the original brief.

---

## ✨ Features (MVP scope: Upload, Parse, Match, Rank)

- **Bulk resume upload** — drag-drop an entire folder; PDF / DOC / DOCX / TXT supported
- **Duplicate detection** — SHA-256 hashing prevents re-parsing the same file
- **AI resume parsing** — OpenAI extracts name, skills, experience, education, certifications, contact, current company, notice period, location, and domain
- **Job definition** — paste a full JD (skills auto-extracted) OR provide a skills list directly
- **Semantic matching** — OpenAI embeddings recognize synonyms (React ≈ ReactJS, Postgres ≈ PostgreSQL, etc.)
- **Weighted scoring** per your spec:
  - Skills 40% · Experience 20% · Education 10% · Domain 10% · Certifications 10% · Location & Notice 10%
- **Skill gap analysis** — matched vs missing skills called out per candidate
- **Excel export** — ranked candidates with full score breakdown, color-coded by tier

---

## 🏗️ Architecture

```
┌─────────────────┐       ┌──────────────────┐       ┌─────────────────┐
│  HTML/JS UI     │──────▶│  FastAPI Backend │──────▶│   OpenAI API    │
│  (drag-drop,    │       │  (Python 3.10+)  │       │ (chat + embed)  │
│   forms, tables)│◀──────│                  │◀──────│                 │
└─────────────────┘       └──────────────────┘       └─────────────────┘
                                  │
                                  ▼
                          ┌──────────────────┐
                          │  JSON Storage    │
                          │  (./data/*.json) │
                          └──────────────────┘
```

### Project layout

```
resume-shortlist/
├── main.py                          # FastAPI entry point (run from here)
├── backend/
│   ├── app/
│   │   ├── config.py                # Env vars, weightages
│   │   ├── models/
│   │   │   └── schemas.py           # Pydantic models
│   │   └── services/
│   │       ├── text_extractor.py    # PDF/DOCX/TXT → text
│   │       ├── resume_parser.py     # OpenAI → CandidateProfile
│   │       ├── openai_client.py     # Shared OpenAI client
│   │       ├── matching_engine.py   # Score & rank candidates
│   │       ├── excel_export.py      # XLSX generation
│   │       └── storage.py           # JSON persistence
│   ├── uploads/                     # Uploaded files (gitignored)
│   ├── data/                        # Persisted candidate/job JSON
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── templates/index.html
│   └── static/
│       ├── style.css
│       └── app.js
├── sample_resumes/                  # 4 sample TXT resumes for testing
└── README.md
```

---

## 🚀 Setup

### 1. Prerequisites

- Python 3.10+
- An [OpenAI API key](https://platform.openai.com/api-keys)

### 2. Install

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
# Edit .env and paste your OPENAI_API_KEY
```

### 4. Run

```bash
# From the resume-shortlist/ directory (project root)
python main.py
# or: uvicorn main:app --reload --port 8000
```

Open **http://localhost:8000** in your browser.

---

## 📖 Usage Walkthrough

1. **Upload resumes** — drag a folder onto the drop zone (or use the "Choose Folder" / "Choose Files" buttons). The system extracts text, parses with Claude, and shows candidate cards.
2. **Define the job** — either:
   - Paste a full job description (Claude auto-extracts required skills), OR
   - Switch to the **Enter Skills** tab and provide a comma-separated list
   - Optionally add min experience, domain, preferred location, preferred education
3. **Click "Save Job & Match Candidates"** — see ranked results with score breakdown, matched/missing skills, and per-candidate recommendation.
4. **Export to Excel** — color-coded ranked list ready for sharing.

### Try it with samples

The `sample_resumes/` folder has 4 TXT resumes — a backend engineer, a fullstack dev, a data scientist, and a junior frontend dev. Upload them and try a job like:

> *Required Skills:* `Python, FastAPI, PostgreSQL, AWS, Docker`
> *Min Experience:* `4`
> *Domain:* `Backend / Cloud`
> *Preferred Location:* `Bangalore`

Expected result: **Priya Sharma ranks #1** (strong skill match + experience + location), **Anjali Verma** second (Python + AWS but data domain), and frontend candidates rank lower.

---

## 🔌 API Reference

| Endpoint                           | Method | Purpose                                  |
| ---------------------------------- | ------ | ---------------------------------------- |
| `/api/resumes/upload`              | POST   | Upload + parse resumes (multipart)       |
| `/api/candidates`                  | GET    | List all parsed candidates               |
| `/api/candidates/{id}`             | GET    | Get a single candidate                   |
| `/api/candidates`                  | DELETE | Wipe all candidates + uploads            |
| `/api/candidates/export/excel`     | GET    | Download all candidates as XLSX          |
| `/api/jobs`                        | POST   | Create a job (form data)                 |
| `/api/jobs`                        | GET    | List all jobs                            |
| `/api/jobs/{id}`                   | GET    | Get a single job                         |
| `/api/match/{job_id}`              | POST   | Score & rank all candidates vs job       |
| `/api/match/{job_id}/export`       | POST   | Download ranked list as XLSX             |
| `/api/health`                      | GET    | Diagnostic info                          |

Interactive docs: **http://localhost:8000/docs**

---

## 🎯 Scoring Logic

| Parameter         | Weight | Source                                                         |
| ----------------- | ------ | -------------------------------------------------------------- |
| Skills            | 40%    | OpenAI embeddings (semantic match w/ synonym recognition)    |
| Experience        | 20%    | Python (deterministic, vs `min_experience_years`)              |
| Education         | 10%    | Python (matches `preferred_education` if set)                  |
| Domain            | 10%    | OpenAI embeddings                                              |
| Certifications    | 10%    | OpenAI embeddings                                              |
| Location & Notice | 10%    | Python (location overlap + notice-period buckets)              |

Weights live in `backend/app/config.py` — tweak freely.

---

## 🛣️ Roadmap (next milestones from your spec)

These are scaffolded into the schema but NOT yet built — flagged as **Optional** in your spec:

- **Workflow Automation** — pipeline stages (screened → interview → offer)
- **Interview Management** — calendar integration, reminders, scheduling
- **Communication Module** — email/SMS automation, recruiter notifications
- **Analytics Dashboard** — funnel metrics, SLA tracking, time-to-hire
- **Auto-shortlisting rules** — threshold-based auto-advance/reject

---

## ⚠️ Production Considerations

This is an **MVP** — for production deployment you'd want:

- **Database** — swap JSON files for PostgreSQL (schemas already Pydantic-ready)
- **Auth** — add user accounts, RBAC for recruiters vs hiring managers
- **Async processing** — large uploads should use a task queue (Celery/RQ)
- **Rate limiting** — protect the Claude API endpoints and your costs
- **OCR** — for scanned-image PDFs (current `pypdf` only extracts text-based PDFs)
- **Object storage** — push uploads to S3/GCS instead of local disk
- **Secrets management** — don't store the API key in `.env` in production
- **Monitoring** — log Claude token usage; the parser costs scale linearly with resume count


