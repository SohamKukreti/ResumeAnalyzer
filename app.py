from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import os
from google import genai
from pdfminer.high_level import extract_text
from docx import Document
from pydantic import BaseModel
from dotenv import load_dotenv
import json

load_dotenv()

class Response(BaseModel):
    JobDescriptionMatch: str
    MissingKeywords: list[str]
    ProfileSummary: str
    PersonalizedSuggestions: list[str]
    ApplicationSuccessRate: str



app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def extract_text_from_pdf(pdf_path):
    return extract_text(pdf_path)

def extract_text_from_docx(docx_path):
    doc = Document(docx_path)
    return "\n".join([para.text for para in doc.paragraphs])

def get_ats_feedback(text, job_description):
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    prompt = f"""
    You are an advanced and highly experienced Applicant Tracking System (ATS) with specialized knowledge across all industries, including but not limited to technology, healthcare, finance, education, manufacturing, retail, and more. Your primary task is to meticulously evaluate resumes against the provided job description. In today's competitive job market, your goal is to offer the best possible guidance for enhancing resumes and increasing candidate success.

    Responsibilities:
    1. Assess resumes with high accuracy based on the provided job description.
    2. Identify and highlight any missing keywords crucial for the role.
    3. Provide a percentage match score (on a scale of 1-100) reflecting the resume's alignment with the job requirements.
    4. Offer detailed feedback for improvements to help candidates stand out.
    5. Analyze the resume, job description, and industry trends to provide personalized suggestions for skills, keywords, and achievements that can enhance the resume.
    6. Recommend improvements for language, tone, and clarity in the resume content.
    7. Provide insights into the performance of the resume by tracking metrics such as application success rates, views, and engagement. Use your extensive, data-trained knowledge to assign an application success rate on a scale of 1-100.

    Note: Every time a user refreshes the page with the same resume and job description, ensure that the result is consistent.

    Field-Specific Customizations:

    General (All Industries):
    You are an advanced and highly experienced ATS with broad expertise across all domains. Evaluate resumes with a focus on industry-specific requirements and adjust your feedback based on the nuances of each field.

    Technology (e.g., Software Engineering, Data Science, Cloud Engineering):
    Evaluate resumes for technology roles by emphasizing technical skills, programming languages, project experience, and familiarity with current industry trends and methodologies.

    Healthcare:
    Evaluate resumes for healthcare roles by focusing on certifications, clinical experience, patient care, compliance with healthcare regulations, and soft skills like empathy and communication.

    Finance:
    For finance roles, assess resumes based on financial acumen, analytical skills, familiarity with financial software, regulatory knowledge, and experience in areas like accounting, investment, or risk management.

    Education:
    Assess resumes for educational roles by emphasizing teaching experience, curriculum development, certification, classroom management, and dedication to fostering student growth.

    Retail/Manufacturing/Other:
    Tailor your evaluation for other fields by focusing on relevant experience, operational skills, customer service, efficiency improvements, and any industry-specific certifications or competencies.

    Resume: {text}
    Description: {job_description}

    I want the response in only the following sectors. Do not include any additional commentary:
    • Job Description Match: \n\n
    • Missing Keywords: \n\n
    • Profile Summary: \n\n
    • Personalized suggestions for skills, keywords, and achievements that can enhance the provided resume: \n\n
    • Application Success Rate: \n\n
    """

    
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=prompt,
        config={
            'response_mime_type': 'application/json',
            'response_schema': list[Response],
        },
    )
    print(response.text)
    return response.text

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_resume():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    job_description = request.form.get('job_description')
    if not job_description:
        return jsonify({"error": "No job description provided"}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    text = ""
    if filename.endswith('.pdf'):
        text = extract_text_from_pdf(filepath)
    elif filename.endswith('.docx'):
        text = extract_text_from_docx(filepath)
    else:
        return jsonify({"error": "Unsupported file format"}), 400
    # print(job_description)
    response_json = get_ats_feedback(text, job_description)
    return response_json