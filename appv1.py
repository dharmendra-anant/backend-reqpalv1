from flask import Flask, request, jsonify, session
from flask_session import Session
from flask_cors import CORS
import openai
import os
import logging
import io
from werkzeug.utils import secure_filename
import tempfile
from datetime import timedelta
from pathlib import Path
from app.pdf_extractor import extract_text_from_pdf
from app.resume_scorer.resume_scorer import score_resume
import json

os.environ["OPENAI_API_KEY"] = "your-openai-key"

app = Flask(__name__)
CORS(app, supports_credentials=True)
# CORS(app, supports_credentials=True, origins=['https://interview.anantgpt.com'])

# Configure session to use filesystem (instead of signed cookies)
app.config['SESSION_TYPE'] = 'filesystem'
# app.config['SESSION_TYPE'] = 'redis'
# app.config['SESSION_TYPE'] = 'cookie'
app.config['SESSION_FILE_DIR'] = 'session_files'  # Directory to store session files
# app.config['SESSION_REDIS'] = redis.from_url('redis://10.71.242.171:6379')
app.config['SESSION_PERMANENT'] = False  # You can configure this as needed
app.config['SESSION_COOKIE_SECURE'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
app.secret_key = 'your_secret_key_here'
# app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', '\default\path')

Session(app)  # Initialize the session

@app.route('/read-jd', methods=['POST'])
def read_jd():
    jd = request.files['file']

    if jd:
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, secure_filename(jd.filename))
        jd.save(temp_path)

        # Convert to Path object
        pdf_path = Path(temp_path)

        text = extract_text_from_pdf(pdf_path)
        return {"text":"\n".join(text.text)}
    else:
        return {"text":"Error"}

@app.route('/score-resumes', methods=['POST'])
def score_resumes():
    if 'resumes_meta' not in request.form:
        return jsonify({"error": "Missing resumes_meta"}), 400

    try:
        resumes_meta = json.loads(request.form['resumes_meta'])
        jd_text = request.form['job_description']
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid resumes_meta JSON"}), 400

    results = []

    for resume_info in resumes_meta:
        field = resume_info.get("field")
        resume_file = request.files.get(field)

        if not resume_file:
            continue  # Skip if the file is missing

        # Save temporarily
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, secure_filename(resume_file.filename))
        resume_file.save(temp_path)

        # Extract text using your existing method
        try:
            content = extract_text_from_pdf(Path(temp_path))
            resume_text = "\n".join(content.text)

            # Score with AI function
            raw_score = score_resume(resume_text, jd_text)  # 0-10
            ai_score = round(raw_score * 10, 2)  # convert to 0-100

            raw_ats_score = ats_score_resume(resume_text, jd_text)
            ats_score = round(raw_ats_score*10, 0)  # ATS score
        except Exception as e:
            print(f"Error processing {resume_file.filename}: {e}")
            continue

        # Build result
        results.append({
            "id": resume_info.get("id"),
            "name": resume_info.get("name"),
            "aiScore": ai_score,
            "atsScore": ats_score,
        })

    return jsonify(results)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port,debug=True, use_reloader=False, threaded = True)
