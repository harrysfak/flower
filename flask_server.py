from flask import Flask, request, jsonify, send_from_directory, abort
import os
from werkzeug.utils import secure_filename

from modelo import Modelo
from modules.config_loader import ConfigLoader
from unziper import Unziper

app = Flask(__name__)

# Ο φάκελος που γράφεις το CSV (ίδιος με self.out_dir του Modelo)
RESULTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "model_results"))
CSV_FILENAME = "results.csv"  # ή "via_predictions.csv" αν έτσι το έσωσες
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
        csv = m.save_csv()
    except Exception as e:
        return f"Detect failed: {e}", 500

    return jsonify({"ok": True, "saved_csv": csv})


@app.route("/download", methods=["GET"])
def download():
    csv_path = os.path.join(RESULTS_DIR, CSV_FILENAME)
    if not os.path.exists(csv_path):
        # Αν δεν έχει δημιουργηθεί ακόμα, 404
        abort(404, description=f"Results file not found: {CSV_FILENAME}")
    # Κατεβάζει ως attachment με σωστό mime type
    return send_from_directory(
        RESULTS_DIR,
        CSV_FILENAME,
        as_attachment=True,
        mimetype="text/csv"
    )


@app.route("/health")
def helth():
    return "Server Alive", 200


if __name__ == "__main__":
    app.run(debug=True)
