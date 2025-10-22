# This is the main Flask application for uploading Excel files and downloading converted CSV files

from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from werkzeug.utils import secure_filename
import os
import subprocess
from pathlib import Path


ALLOWED_EXTENSIONS = {'xls', 'xlsx'}

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / 'uploads'
OUTPUT_DIR = BASE_DIR / 'outputs'
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key") # Replace with a secure key in production

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1) [1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        flash("No file provided")
        return redirect(url_for("index"))
    
    file = request.files["file"]

    if file.filename == "":
        flash("No file selected")
        return redirect(url_for("index"))
    
    if not allowed_file(file.filename):
        flash("Invalid file type. Only .xls and .xlsx are allowed")
        return redirect(url_for("index"))
    
    safe_name = secure_filename(file.filename)
    src_path = UPLOAD_DIR / safe_name
    file.save(src_path)

    # Build the output CSV filename
    base_stem = Path(safe_name).stem
    out_csv = f"{base_stem}.csv"
    out_path = OUTPUT_DIR / out_csv

    # call the transoformer script

    try:
        subprocess.run(
            [
            "python",
            str(BASE_DIR / "converter.py"),
            str(src_path),
            str(out_path),
            ],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        flash(f"conversion failed: {e}")
        return redirect(url_for("index"))
    
    return redirect(url_for("download_file", filename=out_csv))

@app.route("/downloads/<path:filename>")
def download_file(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))