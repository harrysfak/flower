from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse
import os
from pathlib import Path
import shutil

from modelo import Modelo
from modules.config_loader import ConfigLoader
from unziper import Unziper

app = FastAPI()

UPLOAD_FOLDER = ConfigLoader("UPLOAD_FOLDER").load_value()
UNZIP_FOLDER = ConfigLoader("UNZIP_FOLDER").load_value()
MODEL_PATH = ConfigLoader("MODEL_PATH").load_value()  # βάλε εδώ το path του μοντέλου σου

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(UNZIP_FOLDER, exist_ok=True)


def _safe_filename(filename: str) -> str:
    base_name = Path(filename).name
    if not base_name:
        raise HTTPException(status_code=400, detail="No file")
    return base_name


@app.get("/")
def home():
    return {"status": "ok"}


@app.post("/upload")
def upload_file(the_file: UploadFile = File(...)):
    filename = _safe_filename(the_file.filename)
    zip_path = os.path.join(UPLOAD_FOLDER, filename)
    with open(zip_path, "wb") as buffer:
        shutil.copyfileobj(the_file.file, buffer)

    uz = Unziper(zip_path, out_dir=UNZIP_FOLDER)
    uz.unzip()

    return PlainTextResponse("Uploaded", status_code=200)


@app.post("/detect")
def detect_and_save():
    # τρέχει στο UNZIP_FOLDER (εκεί που έβγαλες τις εικόνες)
    m = Modelo(image_dir=UNZIP_FOLDER, out_dir="model_results")
    try:
        m.run_and_dictionarily_write()
        out_path = m.save_txt()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Detect failed: {exc}")

    return {"ok": True, "saved_txt": out_path}


@app.get("/download")
def download():
    raise HTTPException(status_code=501, detail="Not implemented")


@app.get("/health")
def helth():
    return PlainTextResponse("Server Alive", status_code=200)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("flask_server:app", host="0.0.0.0", port=8000, reload=True)
