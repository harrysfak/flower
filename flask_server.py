from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import PlainTextResponse
import aiofiles
import os
from pathlib import Path
from threading import Lock

from modelo import Modelo
from modules.config_loader import ConfigLoader
from unziper import Unziper

app = FastAPI()

UPLOAD_FOLDER = ConfigLoader("UPLOAD_FOLDER").load_value()
UNZIP_FOLDER = ConfigLoader("UNZIP_FOLDER").load_value()
MODEL_PATH = ConfigLoader("MODEL_PATH").load_value()  # βάλε εδώ το path του μοντέλου σου

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(UNZIP_FOLDER, exist_ok=True)

progress_lock = Lock()
UNZIP_PROGRESS = {"status": "idle", "current": 0, "total": 0, "detail": ""}
DETECT_PROGRESS = {"status": "idle", "current": 0, "total": 0, "detail": ""}


def _set_progress(progress, status=None, current=None, total=None, detail=None):
    with progress_lock:
        if status is not None:
            progress["status"] = status
        if current is not None:
            progress["current"] = current
        if total is not None:
            progress["total"] = total
        if detail is not None:
            progress["detail"] = detail


def _progress_payload(progress):
    with progress_lock:
        current = progress.get("current", 0)
        total = progress.get("total", 0)
        status = progress.get("status", "idle")
        detail = progress.get("detail", "")
    percent = 0
    if total:
        percent = int((current / total) * 100)
    return {
        "status": status,
        "current": current,
        "total": total,
        "percent": percent,
        "detail": detail,
    }


def _safe_filename(filename: str) -> str:
    base_name = Path(filename).name
    if not base_name:
        raise HTTPException(status_code=400, detail="No file")
    return base_name.replace("..", "")


@app.get("/")
def home():
    return {"status": "ok"}


@app.post("/upload")
async def upload_file(the_file: UploadFile = File(...)):
    filename = _safe_filename(the_file.filename or "upload.bin")
    zip_path = os.path.join(UPLOAD_FOLDER, filename)

    chunk_size = 1024 * 1024
    try:
        async with aiofiles.open(zip_path, "wb") as buffer:
            while True:
                chunk = await the_file.read(chunk_size)
                if not chunk:
                    break
                await buffer.write(chunk)
    finally:
        await the_file.close()

    def _unzip_progress(current, total):
        _set_progress(UNZIP_PROGRESS, status="running", current=current, total=total)

    _set_progress(UNZIP_PROGRESS, status="running", current=0, total=0, detail="")
    try:
        uz = Unziper(zip_path, out_dir=UNZIP_FOLDER, progress_callback=_unzip_progress)
        await run_in_threadpool(uz.unzip)
        _set_progress(UNZIP_PROGRESS, status="done", detail="Unzip complete")
    except Exception as exc:
        _set_progress(UNZIP_PROGRESS, status="error", detail=str(exc))
        raise HTTPException(status_code=500, detail=f"Unzip failed: {exc}")

    return PlainTextResponse("Uploaded", status_code=200)


@app.post("/detect")
async def detect_and_save():
    # τρέχει στο UNZIP_FOLDER (εκεί που έβγαλες τις εικόνες)
    def _detect_progress(current, total):
        _set_progress(DETECT_PROGRESS, status="running", current=current, total=total)

    _set_progress(DETECT_PROGRESS, status="running", current=0, total=0, detail="")
    try:
        m = Modelo(image_dir=UNZIP_FOLDER, out_dir="model_results")
        await run_in_threadpool(m.run_and_collect, _detect_progress)
        out_path = await run_in_threadpool(m.save_txt)
        via_json, via_csv = await run_in_threadpool(m.export_via_and_csv)
        _set_progress(DETECT_PROGRESS, status="done", detail="Detection complete")
    except Exception as exc:
        _set_progress(DETECT_PROGRESS, status="error", detail=str(exc))
        raise HTTPException(status_code=500, detail=f"Detect failed: {exc}")

    return {"ok": True, "saved_txt": out_path, "via_json": via_json, "via_csv": via_csv}


@app.get("/download")
def download():
    raise HTTPException(status_code=501, detail="Not implemented")

@app.get("/progress/unzip")
def unzip_progress():
    return _progress_payload(UNZIP_PROGRESS)


@app.get("/progress/detect")
def detect_progress():
    return _progress_payload(DETECT_PROGRESS)


@app.get("/health")
def helth():
    return PlainTextResponse("Server Alive", status_code=200)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("flask_server:app", host="0.0.0.0", port=8000, reload=True)
