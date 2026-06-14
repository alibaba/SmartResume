#!/usr/bin/env python3
"""
SmartResume Web Demo
"""

import html
import os
import sys
import tempfile
from pathlib import Path
from flask import Flask, render_template, request, jsonify

# Set environment variables for Hugging Face mirror
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['HF_HUB_ENABLE_HF_TRANSFER'] = '1'

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Ensure process working directory is project root so relative paths work
os.chdir(str(project_root))

from smartresume.backend.resume_analyzer import ResumeAnalyzer  # noqa: E402


MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20MB

# Flask app for serving the HTML template
app = Flask(__name__, template_folder='templates')

# Initialize analyzer once at startup instead of per-request
print("Initializing ResumeAnalyzer (loading models)...")
try:
    analyzer = ResumeAnalyzer(init_ocr=True, init_llm=True)
    print("ResumeAnalyzer initialized with OCR + LLM")
except Exception as e:
    print(f"OCR initialization failed, trying without OCR: {e}")
    analyzer = ResumeAnalyzer(init_ocr=False, init_llm=True)
    print("ResumeAnalyzer initialized with LLM only")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze_resume_SmartResume', methods=['POST'])
def analyze_resume_SmartResume():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    allowed_extensions = {
        '.pdf', '.jpg', '.jpeg', '.png', '.tiff',
        '.webp', '.docx', '.doc', '.txt',
    }
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        supported = ", ".join(allowed_extensions)
        msg = (
            f'Unsupported file type: {file_ext}. '
            f'Supported types: {supported}'
        )
        return jsonify({'error': msg})

    content_length = request.content_length
    if content_length and content_length > MAX_UPLOAD_SIZE:
        max_mb = MAX_UPLOAD_SIZE // (1024 * 1024)
        return jsonify({'error': f'文件过大，最大允许上传 {max_mb}MB'})

    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            file.save(temp_file.name)
            temp_file_path = temp_file.name

        file_size = os.path.getsize(temp_file_path)
        if file_size > MAX_UPLOAD_SIZE:
            max_mb = MAX_UPLOAD_SIZE // (1024 * 1024)
            return jsonify({'error': f'文件过大 ({file_size // (1024*1024)}MB)，最大允许上传 {max_mb}MB'})

        print(f"Processing file: {file.filename} -> {temp_file_path}")

        # Parse resume
        result = analyzer.pipeline(
            cv_path=temp_file_path,
            resume_id="web_demo",
            extract_types=["basic_info", "work_experience", "education"]
        )

        print(f"SmartResume result: {result}")
        print(f"SmartResume result type: {type(result)}")
        result_keys = result.keys() if isinstance(result, dict) else 'Not a dict'
        print(f"SmartResume result keys: {result_keys}")

        if result is None:
            return jsonify({'error': 'Parsing failed, please try again'})

        if "error" in result:
            print(f"Pipeline error: {result['error']}")
            return jsonify({
                'error': 'Resume parsing failed, '
                         'please check the file format and try again'
            })

        # Check key fields
        if 'basicInfo' in result:
            print(f"basicInfo content: {result['basicInfo']}")
        if 'education' in result:
            print(f"education content: {result['education']}")
        if 'workExperience' in result:
            print(f"workExperience content: {result['workExperience']}")

        # Convert to frontend format
        converted_data = convert_SmartResume_to_frontend_format(result)

        print(f"Converted data: {converted_data}")

        return jsonify(converted_data)

    except Exception as e:
        print(f"Error processing file {file.filename}: {e}")
        return jsonify({
            'error': 'An internal error occurred while processing the resume'
        })
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                print(f"Cleaned up temporary file: {temp_file_path}")
            except Exception as e:
                print(f"Error cleaning up temporary file {temp_file_path}: {e}")


def _sanitize_value(value):
    """Escape HTML special characters in string values to prevent XSS."""
    if isinstance(value, str):
        return html.escape(value, quote=True)
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, dict):
        return {k: _sanitize_value(v) for k, v in value.items()}
    return value


def convert_SmartResume_to_frontend_format(SmartResume_result):
    converted_data = {
        "basicInfo": {},
        "education": [],
        "workExperience": []
    }

    try:
        # Basic info - use basicInfo field directly
        if 'basicInfo' in SmartResume_result and SmartResume_result['basicInfo']:
            info = SmartResume_result['basicInfo']
            converted_data["basicInfo"] = {
                "name": info.get('name', ''),
                "personalEmail": info.get('personalEmail', ''),
                "phoneNumber": info.get('phoneNumber', ''),
                "age": info.get('age', ''),
                "gender": info.get('gender', ''),
                "born": info.get('born', ''),
                "currentLocation": info.get('currentLocation', ''),
                "placeOfOrigin": info.get('placeOfOrigin', ''),
                "desiredLocation": (
                    info.get('desiredLocation', [])
                    if isinstance(info.get('desiredLocation'), list)
                    else info.get('desiredLocation', '')
                )
            }

        # Education - use education field directly
        if 'education' in SmartResume_result and SmartResume_result['education']:
            for edu in SmartResume_result['education']:
                if edu:
                    converted_edu = {
                        "school": edu.get('school', ''),
                        "major": edu.get('major', ''),
                        "degreeLevel": edu.get('degreeLevel', ''),
                        "department": edu.get('department', ''),
                        "period": {
                            "startDate": edu.get('period', {}).get('startDate', ''),
                            "endDate": edu.get('period', {}).get('endDate', '')
                        },
                        "educationDescription": edu.get('educationDescription', '')
                    }
                    converted_data["education"].append(converted_edu)

        # Work experience - use workExperience field directly
        if 'workExperience' in SmartResume_result and SmartResume_result['workExperience']:
            for work in SmartResume_result['workExperience']:
                if work:
                    converted_work = {
                        "companyName": work.get('companyName', ''),
                        "position": work.get('position', ''),
                        "employmentPeriod": {
                            "startDate": work.get('employmentPeriod', {}).get('startDate', ''),
                            "endDate": work.get('employmentPeriod', {}).get('endDate', '')
                        },
                        "jobDescription": work.get('jobDescription', ''),
                        "internship": work.get('internship', 0)
                    }
                    converted_data["workExperience"].append(converted_work)

        print("Successfully converted SmartResume result to frontend format")

    except Exception as e:
        print(f"Error converting SmartResume result: {e}")
        import traceback
        traceback.print_exc()
        pass

    return _sanitize_value(converted_data)


if __name__ == "__main__":
    # Start Flask application
    app.run(debug=False, host="0.0.0.0", port=4999)
