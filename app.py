import os
import subprocess
import shutil
import uuid
import tempfile
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from PIL import Image

# Base temp dir (usually /tmp inside container)
BASE_TEMP = tempfile.gettempdir()

app = Flask(__name__)
CORS(app)


def is_image(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"]


def is_video(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in [".mp4", ".mkv", ".mov", ".avi", ".flv"]
def is_audio(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in [".mp3", ".wav", ".ogg", ".aac", ".flac"]

@app.route("/upload", methods=["POST"])
def upload_files():
    if "files" not in request.files:
        return jsonify({"error": "No files uploaded"}), 400
    
    files = request.files.getlist("files")
    fmt = request.form.get("format", "mp4")  # default to mp4

    # Create unique session dir inside /tmp
    session_id = str(uuid.uuid4())[:8]
    session_dir = os.path.join(BASE_TEMP, f"convert_{session_id}")
    upload_dir = os.path.join(session_dir, "uploads")
    converted_dir = os.path.join(session_dir, "converted")
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(converted_dir, exist_ok=True)

    converted_files = []

    for file in files:
        filename = secure_filename(file.filename)
        input_path = os.path.join(upload_dir, filename)
        file.save(input_path)

        base, _ = os.path.splitext(filename)
        output_file = f"{base}.{fmt}"
        output_path = os.path.join(converted_dir, output_file)

        try:
            if is_image(filename):
                # Convert image using Pillow
                with Image.open(input_path) as img:
                    img = img.convert("RGB") if fmt.lower() in ["jpg", "jpeg", "bmp"] else img
                    img.save(output_path, fmt.upper())
            
            elif is_video(filename):
                # Convert video/audio using ffmpeg
                cmd = ["ffmpeg", "-y", "-i", input_path, output_path]
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            elif is_audio(filename):
                # Convert video/audio using ffmpeg
                cmd = ["ffmpeg", "-y", "-i", input_path, output_path]
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            else:
                return jsonify({"error": f"Unsupported file type: {filename}"}), 400

            converted_files.append(output_file)

        except Exception as e:
            return jsonify({"error": f"Conversion failed for {filename}: {str(e)[:200]}"}), 500

    # Zip everything
    zip_name = f"converted_{session_id}.zip"
    zip_path = os.path.join(session_dir, zip_name)
    shutil.make_archive(zip_path.replace(".zip", ""), "zip", converted_dir)

    return jsonify({
        "message": "Batch conversion complete",
        "files": converted_files,
        "zip_url": f"/download_zip/{session_id}/{zip_name}"
    })


@app.route("/download_zip/<session_id>/<filename>", methods=["GET"])
def download_zip(session_id, filename):
    session_dir = os.path.join(BASE_TEMP, f"convert_{session_id}")
    zip_path = os.path.join(session_dir, filename)

    if not os.path.exists(zip_path):
        return jsonify({"error": "Zip not found"}), 404

    return send_file(zip_path, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

