from flask import Flask, render_template, request, jsonify
import os
from werkzeug.utils import secure_filename
import fitz 
import openai 

openai.api_key = "your_openai_api_key_here"
ASSISTANT_ID = "asst_VYWD4lWBcZ5giMb3OYOWmqMt"

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok = True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["ALLOWED_EXTENSIONS"] = {"pdf"}

new_instructions = """
You are a **medical report analysis assistant** responsible for analyzing and summarizing a patient's medical report. Your goal is to:
1. **Determine whether the patient's status is Normal or Abnormal.**
2. **Summarize any test abnormalities and provide structured medical recommendations.**

## **Key Analysis Steps:**
- Read the entire document carefully.
- Prioritize analyzing the **'Interpretation'** and **'Impression'** sections first.
- If these sections are missing or insufficient, use relevant data from the entire document.
- Extract the **name of the scan or test performed** from the document.
- Focus only on the **Test, Result, and Recommended Range** columns in lab test reports.
- Identify abnormalities but **do not display numeric values** of test results or reference ranges.

## **Output Format (Strictly Follow This Every Time):**
### **Scan/Test Information**
- **Scan/Test Name:** [Extracted from the document]
- **Patient Status:** [Normal / Abnormal]

### **Medical Summary (Only if Status is Abnormal)**
- **Name of the Patient:**[Name of the patient from report]
- **Age:**[Age of the patient]
- **Gender:**[Gender of the patient]

- **Expected Diseases/Conditions:**  
  - List abnormalities detected, each with a **concise one-line explanation**:
    - Expected disease or condition
    - A short, simple explanation of why it occurred
    - How a doctor identifies it based on test results (**without mentioning values**)

### **Wellness & Treatment Plan (For Abnormal Cases Only)**
- **Dietary Advice:**  
  - Specific diet recommendations based on detected abnormalities.
- **Physical Health Recommendations:**  
  - Appropriate activity guidelines.
- **Medications:**  
  - List of required medications, if applicable.
- **Follow-up & Review Plan:**  
  - Necessary future tests, treatments, or specialist consultations.

## **Strict Instructions:**
- **Do not include Systematic Review, Medical History, Chief Complaints, or Personal History.**
- **Do not display "Test Result vs Recommended Range" in the output.**
- **Do not include normal test results.**
- **Ensure diseases are identified as a doctor would based on test abnormalities.**
- **Do not add irrelevant information or provide internal responses.**
- **Ensure the output follows this exact format every time.**
"""
def allowed_file(filename):
    return "." in filename and filename.rsplit(".",1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]

def extract_text_from_pdf(pdf_path):
    print(f"Checking file existence: {pdf_path}")
    
    if not os.path.exists(pdf_path) or os.path.getsize(pdf_path) == 0:
        return "Error : The file is empty and does not exist"
    
    doc = fitz.open(pdf_path)
    texts = []
    for page in doc:
        page_text = page.get_text("text")
        if page_text:
            texts.append(page_text)
    text = "\n".join(texts)
    return text.strip() if text else "Error : No text found in PDF"

def analyze_pdf_with_assistant(pdf_path):
    if not os.path.exists(pdf_path):
        return f"Error: File not found - {pdf_path}"
    
    report_text = extract_text_from_pdf(pdf_path)
    if report_text.startswith("Error"):
        return report_text
    
    print("Extracted text from PDF.")
    
    full_prompt = f"{new_instructions}\n\nReport Text:\n{report_text}"
    
    thread_response = openai.beta.threads.create()
    thread_id = thread_response.id
    
    openai.beta.threads.messages.create(
        thread_id=thread_id,
        role = "user",
        content = full_prompt
    )
    print("Running assistant and waiting for response...")
    run_response = openai.beta.threads.runs.create_and_poll(
        thread_id = thread_id,
        assistant_id = ASSISTANT_ID
    )
    print("Run response:",run_response)
    
    messages = openai.beta.threads.messages.list(thread_id = thread_id)
    print(messages)
    assistant_response = None
    for message in messages.data:
        if message.role == "assistant":
            assistant_response = message.content[0].text.value.strip()
            print(assistant_response, "response")
            break
    
    # os.remove(pdf_path)    
    
    # return assistant_response if assistant_response else "Error: No assistant response received."
    if assistant_response is None:
        return "Error : No assistant response received."
    
    print("Assistant response:", assistant_response)
    return assistant_response

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze_pdf", methods = ["POST"])
def analyze():
    if "pdf_file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    pdf_file = request.files["pdf_file"]
    if pdf_file.filename == "":
        return jsonify({"error" :"No selected file"}), 400
    if not allowed_file(pdf_file.filename):
        return jsonify({"error": "Invalid file format. Only PDFs are allowed."}), 400

    filename = secure_filename(pdf_file.filename)
    
    upload_folder = app.config.get("UPLOAD_FOLDER", "uploads")
    pdf_path = os.path.join(upload_folder, filename)
    abs_pdf_path = os.path.abspath(pdf_path)
    pdf_file.save(abs_pdf_path)
    print(f"Saved PDF to: {abs_pdf_path}")
    
    result = analyze_pdf_with_assistant(abs_pdf_path)
    print("Final result:", result)
    return jsonify({"result": result}), 200


if __name__ == "__main__":
    print("Medical Analysis is Running at http://127.0.0.1:5000/")
    app.run(debug = True)
