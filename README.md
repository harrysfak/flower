# Flower Detection Service

A small project that uploads a ZIP of images, unzips them, runs a detection model, and returns the saved results. The HTTP API is now built with **FastAPI**.

## Requirements

Install dependencies (ideally in a virtual environment):

```bash
pip install -r requirements
```

## Configuration

The server relies on values stored in `assets/cfg.json`, which are loaded by `modules/config_loader.py`.
Update `CONFIG_PATH` in `modules/config_loader.py` to point to your local `assets/cfg.json` if needed.

Expected keys in `cfg.json`:

- `UPLOAD_FOLDER`
- `UNZIP_FOLDER`
- `MODEL_PATH`

## Run the API server

Option 1 (recommended):

```bash
uvicorn flask_server:app --reload --host 0.0.0.0 --port 8000
```

Option 2 (convenience entrypoint):

```bash
python flask_server.py
```

## API Endpoints

- `GET /` → health probe response
- `GET /health` → `Server Alive`
- `POST /upload` → multipart form upload (`the_file`) of a ZIP
- `POST /detect` → runs the model and returns `{ ok, saved_txt, via_json, via_csv }`
- `GET /progress/unzip` → unzip progress (`status`, `percent`, `current`, `total`)
- `GET /progress/detect` → model progress (`status`, `percent`, `current`, `total`)

## GUI client

The Tkinter client in `main.py` can upload ZIPs and run detections against the API server.
Make sure the server is running before using the GUI.
