from flask import Flask, request, render_template_string, jsonify
import os
from werkzeug.utils import secure_filename

from modelo import Modelo
from modules.config_loader import ConfigLoader
from unziper import Unziper

app = Flask(__name__)

UPLOAD_FOLDER = ConfigLoader("UPLOAD_FOLDER").load_value()
UNZIP_FOLDER = ConfigLoader("UNZIP_FOLDER").load_value()
MODEL_PATH = ConfigLoader("MODEL_PATH").load_value()  # βάλε εδώ το path του μοντέλου σου

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(UNZIP_FOLDER, exist_ok=True)



@app.route("/")
def home():
    return "<h1> OK </h1>"

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

    return "Uploaded", 200

@app.post("/detect")
def detect_and_save():
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


@app.route("/health")
def helth():
    return "Server Alive", 200

if __name__ == "__main__":
    app.run(debug=True)
