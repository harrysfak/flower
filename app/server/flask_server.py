import uuid
import shutil
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, abort
import os
from werkzeug.utils import secure_filename

from app.server.helpers.find_img import find_image_dir
from app.server.modules.file_manager import FileManager
from app.server.modules.modelo import Modelo
from app.server.modules.config_loader import ConfigLoader
from app.server.modules.unziper import Unziper

app = Flask(__name__)

# Ο φάκελος που γράφεις το CSV (ίδιος με self.out_dir του Modelo)
CSV_FILENAME = "results.csv"  # ή "via_predictions.csv" αν έτσι το έσωσες
RESULTS_DIR = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../model_results")))

BASE_DIR = Path(__file__).resolve().parent  # .../app/server

UPLOAD_FOLDER = Path(ConfigLoader("UPLOAD_FOLDER").load_value())
UNZIP_FOLDER  = Path(ConfigLoader("UNZIP_FOLDER").load_value())

# Αν τα config values είναι relative (π.χ. "uploads"), τα κάνουμε relative στο server folder
if not UPLOAD_FOLDER.is_absolute():
    UPLOAD_FOLDER = BASE_DIR / UPLOAD_FOLDER
if not UNZIP_FOLDER.is_absolute():
    UNZIP_FOLDER = BASE_DIR / UNZIP_FOLDER

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
UNZIP_FOLDER.mkdir(parents=True, exist_ok=True)


@app.route("/")
def home():
    return "<h1> OK </h1>"


@app.post("/upload")
def upload_file():
    uploaded = request.files.get("the_file")
    if not uploaded or uploaded.filename == "":
        return jsonify({"ok": False, "error": "No file"}), 400

    original_name = secure_filename(uploaded.filename)
    dataset_id = uuid.uuid4().hex[:10]  # π.χ. a3f91c2d10

    zip_filename = f"{dataset_id}__{original_name}"
    zip_path = UPLOAD_FOLDER / zip_filename
    uploaded.save(str(zip_path))

    extract_dir = UNZIP_FOLDER / dataset_id
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    extract_dir.mkdir(parents=True, exist_ok=True)

    uz = Unziper(str(zip_path), out_dir=str(extract_dir))
    uz.unzip()

    return jsonify({"ok": True, "dataset_id": dataset_id}), 200

@app.post("/detect")
def detect_and_save():
    data = request.get_json(silent=True) or {}
    dataset_id = data.get("dataset_id")
    if not dataset_id:
        return jsonify({"ok": False, "error": "dataset_id required"}), 400

    dataset_root = UNZIP_FOLDER / dataset_id
    if not dataset_root.exists():
        return jsonify({"ok": False, "error": f"Unzip folder not found for {dataset_id}"}), 404

    try:
        image_dir = find_image_dir(dataset_root)  # <-- εδώ το fix
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

    csv_name = f"results__{dataset_id}.csv"
    m = Modelo(image_dir=str(image_dir), out_dir=str(RESULTS_DIR))

    try:
        m.run_and_dictionarily_write()
        if "filename" in m.save_csv.__code__.co_varnames:
            m.save_csv(filename=csv_name)
        else:
            m.save_csv()
    except Exception as e:
        return jsonify({"ok": False, "error": f"Detect failed: {e}"}), 500

    return jsonify({"ok": True, "dataset_id": dataset_id, "csv": csv_name, "image_dir": str(image_dir)}), 200

@app.get("/download")
def download():
    dataset_id = request.args.get("dataset_id")
    if not dataset_id:
        return jsonify({"ok": False, "error": "dataset_id required"}), 400

    csv_filename = f"results__{dataset_id}.csv"
    csv_path = RESULTS_DIR / csv_filename
    if not csv_path.exists():
        abort(404, description=f"Results file not found: {csv_filename}")

    return send_from_directory(
        str(RESULTS_DIR),
        csv_filename,
        as_attachment=True,
        mimetype="text/csv"
    )


@app.post("/reset")
def reset_workspace():
    try:
        deleted_uploads = FileManager(str(UPLOAD_FOLDER)).reset_memory()
        deleted_unzip   = FileManager(str(UNZIP_FOLDER)).reset_memory()
        deleted_results = FileManager(str(RESULTS_DIR)).reset_memory()

        return jsonify({
            "ok": True,
            "deleted": {
                "uploads": len(deleted_uploads),
                "unzip": len(deleted_unzip),
                "results": len(deleted_results),
            }
        }), 200

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/health")
def helth():
    return "Server Alive", 200


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )

