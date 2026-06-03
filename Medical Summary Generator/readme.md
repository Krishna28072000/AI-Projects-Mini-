# Medical Report Analysis Assistant

A Flask-based web application that allows users to upload medical report PDFs and analyze them using the OpenAI Responses API. The application extracts text from the uploaded PDF, sends the report content to OpenAI, and returns a structured medical summary.

> **Important:** This application is intended to assist with medical report understanding. It should not replace professional medical diagnosis, treatment, or consultation with a qualified doctor.

---

## Features

- Upload medical report PDFs through a Flask web interface.
- Extract text from PDF files using PyMuPDF.
- Analyze reports using the OpenAI Responses API.
- Identify whether the patient report appears **Normal** or **Abnormal**.
- Extract scan/test name, patient details, abnormalities, wellness advice, and follow-up recommendations.
- Returns a clean JSON response from the backend.
- Uses the latest OpenAI SDK style instead of the older Assistants/Threads API.

---

## Tech Stack

- **Backend:** Python, Flask
- **PDF Text Extraction:** PyMuPDF (`fitz`)
- **AI Integration:** OpenAI Responses API
- **File Upload Handling:** Werkzeug
- **Response Format:** JSON

---

## Project Structure

```text
medical-report-analysis/
│
├── app.py
├── uploads/
├── templates/
│   └── index.html
├── requirements.txt
└── README.md
```

---

## Prerequisites

Make sure you have the following installed:

- Python 3.9 or above
- pip
- OpenAI API key

---

## Installation

### 1. Clone or Download the Project

```bash
git clone <your-repository-url>
cd medical-report-analysis
```

Or place the project files manually inside your preferred folder.

---

### 2. Create a Virtual Environment

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

If you do not have a `requirements.txt` file yet, create one with:

```txt
flask
openai
PyMuPDF
werkzeug
```

Then run:

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Set your OpenAI API key as an environment variable.

### Windows CMD

```cmd
set OPENAI_API_KEY=your_openai_api_key_here
```

### Windows PowerShell

```powershell
$env:OPENAI_API_KEY="your_openai_api_key_here"
```

### Linux / macOS

```bash
export OPENAI_API_KEY="your_openai_api_key_here"
```

---

## OpenAI Model Configuration

Inside `app.py`, the model is configured using:

```python
OPENAI_MODEL = "gpt-4.1-mini"
```

You can change it based on your requirement:

```python
OPENAI_MODEL = "gpt-4.1"
```

or

```python
OPENAI_MODEL = "gpt-4o-mini"
```

For production, choose a model based on cost, latency, and accuracy requirements.

---

## Running the Application

Start the Flask server:

```bash
python app.py
```

The application will run at:

```text
http://127.0.0.1:5000/
```

Open this URL in your browser.

---

## API Endpoint

### Analyze PDF

```http
POST /analyze_pdf
```

### Request Type

`multipart/form-data`

### Form Field

| Field Name | Type | Required | Description |
|---|---|---|---|
| `pdf_file` | File | Yes | Medical report PDF file |

### Example Using cURL

```bash
curl -X POST http://127.0.0.1:5000/analyze_pdf \
  -F "pdf_file=@sample_report.pdf"
```

### Successful Response

```json
{
  "result": "### Scan/Test Information\n- **Scan/Test Name:** ...\n- **Patient Status:** Abnormal\n..."
}
```

### Error Response

```json
{
  "error": "No file uploaded"
}
```

or

```json
{
  "error": "Invalid file format. Only PDFs are allowed."
}
```

---

## How It Works

1. The user uploads a PDF file from the web interface.
2. The Flask backend validates that the uploaded file is a PDF.
3. The file is saved inside the `uploads/` directory.
4. PyMuPDF extracts text from the report.
5. The extracted text is passed to the OpenAI Responses API.
6. OpenAI analyzes the report using strict medical-summary instructions.
7. The final structured summary is returned to the frontend as JSON.

---

## Responses API Usage

The older Assistants API flow using:

```python
openai.beta.threads.create()
openai.beta.threads.messages.create()
openai.beta.threads.runs.create_and_poll()
```

has been replaced with the Responses API:

```python
response = client.responses.create(
    model=OPENAI_MODEL,
    instructions=new_instructions,
    input=[
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": f"Analyze the following medical report:\n\n{report_text}"
                }
            ]
        }
    ],
    temperature=0.2,
)

assistant_response = response.output_text.strip()
```

This makes the application simpler, faster, and easier to maintain.

---

## Security Notes

For production use, make sure to follow these practices:

- Do not hardcode API keys in the source code.
- Store API keys in environment variables or a secure secret manager.
- Restrict uploaded file size.
- Validate PDF file types properly.
- Delete uploaded files after processing if long-term storage is not required.
- Avoid logging sensitive patient information.
- Use HTTPS in production.
- Add user authentication if patient data is being processed.
- Follow applicable healthcare data privacy regulations.

---

## Recommended Production Improvements

- Add file size validation.
- Add OCR support for scanned PDFs.
- Add request rate limiting.
- Add structured logging.
- Store analysis history in a database.
- Add authentication and role-based access.
- Move instructions into a separate prompt file.
- Add Docker support.
- Add unit tests.
- Add frontend loading and error states.
- Deploy using Gunicorn or Uvicorn behind Nginx.

---

## Common Issues

### 1. `OPENAI_API_KEY` Not Found

Make sure the environment variable is set before running the application.

```bash
export OPENAI_API_KEY="your_openai_api_key_here"
```

### 2. No Text Found in PDF

Some PDFs are scanned images and do not contain selectable text. In that case, OCR is required.

Recommended OCR options:

- Tesseract OCR
- Azure Document Intelligence
- Google Document AI
- AWS Textract

### 3. OpenAI API Error

Check:

- API key is valid.
- Model name is correct.
- Internet connection is working.
- Your OpenAI account has sufficient credits or access.

---

## Disclaimer

This application provides AI-generated medical report summaries for informational and assistance purposes only. The output should always be reviewed by a qualified healthcare professional before making any medical decision.

