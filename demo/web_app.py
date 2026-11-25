from importlib import import_module
from threading import Lock
from uuid import uuid4
import os
import sys
import tempfile
from pathlib import Path
from flask import Flask, render_template, request, jsonify


os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"


project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


os.chdir(str(project_root))

ResumeAnalyzer = import_module(
    "smartresume.backend.resume_analyzer"
).ResumeAnalyzer
_schema = import_module("smartresume.utils.extraction_schema")
EXTRACT_TYPES = _schema.EXTRACT_TYPES
complete_resume = _schema.complete_resume


MAX_UPLOAD_SIZE = 20 * 1024 * 1024


app = Flask(__name__, template_folder="templates")
analyzer_lock = Lock()
UPLOAD_DIR = project_root / "temp" / "web_uploads"


print("Initializing ResumeAnalyzer (loading models)...")
try:
    analyzer = ResumeAnalyzer(init_ocr=True, init_llm=True)
    print("ResumeAnalyzer initialized with OCR + LLM")
except Exception as e:
    print(f"OCR initialization failed, trying without OCR: {e}")
    analyzer = ResumeAnalyzer(init_ocr=False, init_llm=True)
    print("ResumeAnalyzer initialized with LLM only")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze_resume_SmartResume", methods=["POST"])
def analyze_resume_SmartResume():
    if "file" not in request.files:
        return jsonify({"error": "No file part"})

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"})

    allowed_extensions = {
        ".pdf",
        ".jpg",
        ".jpeg",
        ".png",
        ".tiff",
        ".webp",
        ".docx",
        ".doc",
        ".txt",
    }
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        supported = ", ".join(allowed_extensions)
        msg = (
            f"Unsupported file type: {file_ext}. "
            f"Supported types: {supported}"
        )
        return jsonify({"error": msg})

    content_length = request.content_length
    if content_length and content_length > MAX_UPLOAD_SIZE:
        max_mb = MAX_UPLOAD_SIZE // (1024 * 1024)
        return jsonify({"error": f"文件过大，最大允许上传 {max_mb}MB"})

    temp_file_path = None
    try:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=file_ext, dir=UPLOAD_DIR
        ) as temp_file:
            file.save(temp_file.name)
            temp_file_path = temp_file.name

        file_size = os.path.getsize(temp_file_path)
        if file_size > MAX_UPLOAD_SIZE:
            max_mb = MAX_UPLOAD_SIZE // (1024 * 1024)
            size_mb = file_size // (1024 * 1024)
            message = f"文件过大 ({size_mb}MB)，最大允许上传 {max_mb}MB"
            return jsonify({"error": message})

        print(f"Processing file: {file.filename} -> {temp_file_path}")

        with analyzer_lock:
            result = analyzer.pipeline(
                cv_path=temp_file_path,
                resume_id="web_" + uuid4().hex,
                extract_types=list(EXTRACT_TYPES),
            )

        if result is None:
            return jsonify({"error": "Parsing failed, please try again"})

        if "error" in result:
            print(f"Pipeline error: {result['error']}")
            return jsonify(
                {
                    "error": "Resume parsing failed, "
                    "please check the file format and try again"
                }
            )

        converted_data = convert_SmartResume_to_frontend_format(result)

        return jsonify(converted_data)

    except Exception as e:
        print(f"Error processing file {file.filename}: {e}")
        return jsonify(
            {"error": "An internal error occurred while processing the resume"}
        )
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                print(f"Cleaned up temporary file: {temp_file_path}")
            except Exception as e:
                print(
                    f"Error cleaning up temporary file {temp_file_path}: {e}"
                )


def convert_SmartResume_to_frontend_format(SmartResume_result):

    if not isinstance(SmartResume_result, dict):
        raise TypeError("Resume result must be a JSON object")
    return complete_resume(SmartResume_result)


if __name__ == "__main__":

    app.run(debug=False, host="0.0.0.0", port=4999)
