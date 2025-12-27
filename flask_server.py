from flask import Flask, request, render_template_string, jsonify
import os
from werkzeug.utils import secure_filename

from modelo import Modelo
from unziper import Unziper

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
UNZIP_FOLDER = "unzip"
MODEL_PATH = "best.pt"  # βάλε εδώ το path του μοντέλου σου

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(UNZIP_FOLDER, exist_ok=True)


@app.post("/upload")
def upload_file():
    uploaded = request.files.get("the_file")
    if not uploaded or uploaded.filename == "":
        return "No file", 400

    filename = secure_filename(uploaded.filename)
    zip_path = os.path.join(UPLOAD_FOLDER, filename)
    uploaded.save(zip_path)

    uz = Unziper(zip_path, out_dir=UNZIP_FOLDER)
    uz.unzip()

    return "Upload OK. Now click: Run Detect"

@app.post("/detect")
def detect_save():
    # τρέχει στο UNZIP_FOLDER (εκεί που έβγαλες τις εικόνες)
    m = Modelo(image_dir=UNZIP_FOLDER, out_dir="model_results")
    try:
        m.run_and_dictionarily_write()
        out_path = m.save_txt()
    except Exception as e:
        return f"Detect failed: {e}", 500

    return jsonify({"ok": True, "saved_txt": out_path})



@app.route("/download")
def download():
    return  #how to download via_predictions
if __name__ == "__main__":
    app.run(debug=True)
