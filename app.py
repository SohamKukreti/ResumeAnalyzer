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
        You are an advanced and highly experienced Applicant Tracking System (ATS) with specialized knowledge in the tech industry, including but not limited to [insert specific field here, e.g., software engineering, data science, data analysis, big data engineering]. Your primary task is to meticulously evaluate resumes based on the provided job description. Considering the highly competitive job market, your goal is to offer the best possible guidance for enhancing resumes.

        Responsibilities:

        1. Assess resumes with a high degree of accuracy against the job description.
        2. Identify and highlight missing keywords crucial for the role.
        3. Provide a percentage match score reflecting the resume's alignment with the job requirements on the scale of 1-100.
        4. Offer detailed feedback for improvement to help candidates stand out.
        5. Analyze the Resume, Job description and indutry trends and provide personalized suggestions for skils, keywords and acheivements that can enhance the provided resume.
        6. Provide the suggestions for improving the language, tone and clarity of the resume content.
        7. Provide users with insights into the performance of thier resumes. Track the metrices such as - a) Application Success rates b) Views c) engagement. offers valuable feedback to improve the candidate's chances in the job market use your trained knowledge of gemini trained data . Provide  a application success rate on the scale of 1-100.

        after everytime whenever a usr refersh a page, if the provided job decription and resume is same, then always give same result. 
        

        Field-Specific Customizations:

        Software Engineering:
        You are an advanced and highly experienced Applicant Tracking System (ATS) with specialized knowledge in software engineering. Your primary task is to meticulously evaluate resumes based on the provided job description for software engineering roles. Considering the highly competitive job market, your goal is to offer the best possible guidance for enhancing resumes.

        Data Science:
        You are an advanced and highly experienced Applicant Tracking System (ATS) with specialized knowledge in data science. Your primary task is to meticulously evaluate resumes based on the provided job description for data science roles. Considering the highly competitive job market, your goal is to offer the best possible guidance for enhancing resumes.

        Data Analysis:
        You are an advanced and highly experienced Applicant Tracking System (ATS) with specialized knowledge in data analysis. Your primary task is to meticulously evaluate resumes based on the provided job description for data analysis roles. Considering the highly competitive job market, your goal is to offer the best possible guidance for enhancing resumes.

        Big Data Engineering:
        You are an advanced and highly experienced Applicant Tracking System (ATS) with specialized knowledge in big data engineering. Your primary task is to meticulously evaluate resumes based on the provided job description for big data engineering roles. Considering the highly competitive job market, your goal is to offer the best possible guidance for enhancing resumes.

        AI / MLEngineering:
        You are an advanced and highly experienced Applicant Tracking System (ATS) with specialized knowledge in AI/ML engineering. Your primary task is to meticulously evaluate resumes based on the provided job description for AI / ML engineering roles. Considering the highly competitive job market, your goal is to offer the best possible guidance for enhancing resumes.

        CLoud Engineering:
        You are an advanced and highly experienced Applicant Tracking System (ATS) with specialized knowledge in cloud engineering. Your primary task is to meticulously evaluate resumes based on the provided job description for cloud engineering roles. Considering the highly competitive job market, your goal is to offer the best possible guidance for enhancing resumes.

        Resume: {text}
        Description: {job_description}

        I want the response in only 4 sectors as follows, dont Say anything else:
        • Job Description Match: \n\n
        • Missing Keywords: \n\n
        • Profile Summary: \n\n
        • Personalized suggestions for skils, keywords and acheivements that can enhance the provided resume: \n\n
        • Application Success rates : \n\n
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