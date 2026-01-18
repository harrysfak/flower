import csv
import json
from pathlib import Path

import psutil
from tqdm import tqdm
from ultralytics import YOLO
import os

from app.server.modules.cpu_check import CPU_LIMIT, CPULimitExceeded


class Modelo:

    def __init__(self, image_dir, modelo="best.pt", out_dir="model_results"):
        here = Path(__file__).resolve().parent  # .../app/server/modules
        modelo_path = Path(modelo)

        # αν δώσεις "best.pt" (relative), ψάξε το δίπλα στον server φάκελο
        if not modelo_path.is_absolute():
            modelo_path = (here.parent / modelo_path).resolve()  # .../app/server/best.pt

        if not modelo_path.exists():
            raise FileNotFoundError(f"Model not found: {modelo_path}")

        print(f"Model path: {modelo_path}")
        self.model = YOLO(str(modelo_path))

        self.image_dir = image_dir
        if not os.path.isdir(self.image_dir):
            raise NotADirectoryError(f"Image dir not found: {self.image_dir}")

        self.out_dir = out_dir
        os.makedirs(out_dir, exist_ok=True)

        self.via_export = {}

        exts = (".jpg", ".jpeg", ".png")
        self.list_of_img = [f for f in os.listdir(self.image_dir) if f.lower().endswith(exts)]

    def run_and_dictionarily_write(self):

        for im in tqdm(self.list_of_img, desc="Predicting", colour="green", unit="img"):
            # CPU CHECK
            cpu = psutil.cpu_percent(interval=0.2)
            if cpu > CPU_LIMIT:
                print(f"\n⛔ CPU {cpu}% exceeded → stopping early")
                raise CPULimitExceeded(f"CPU {cpu}% exceeded")

            image_path = os.path.join(self.image_dir, im)
            file_size = os.path.getsize(image_path)  # απαιτείται από VIA για το 'size'

            preds = self.model.predict(image_path, verbose=False)
            r0 = preds[0]
            boxes = r0.boxes
            n_bx = len(boxes) if boxes is not None else 0

            # --- αν θες να κρατήσεις και την παλιά σύνοψη, άφησε την επόμενη γραμμή· αλλιώς σβήσε την ---
            # self.results[f"{im}"] = f"Detections : {n_bx}"

            # --- VGG/VIA JSON ---
            img_id = f"{im}{file_size}"  # κοινό pattern στο VIA 1.x: filename+size ως unique id
            regions = []

            if boxes is not None and n_bx > 0:
                class_names = self.model.names  # mapping index -> class name
                for b in boxes:
                    # πάρε τις συντεταγμένες ως xyxy
                    x1, y1, x2, y2 = [float(v) for v in b.xyxy[0].tolist()]
                    x = int(round(min(x1, x2)))
                    y = int(round(min(y1, y2)))
                    w = int(round(abs(x2 - x1)))
                    h = int(round(abs(y2 - y1)))

                    # κλάση & confidence (όπου υπάρχουν)
                    cls_idx = int(b.cls[0].item()) if hasattr(b, "cls") else None
                    cls_name = class_names.get(cls_idx, str(cls_idx)) if cls_idx is not None else "object"
                    conf = float(b.conf[0].item()) if hasattr(b, "conf") else ""

                    regions.append({
                        "shape_attributes": {
                            "name": "rect",
                            "x": x, "y": y, "width": w, "height": h
                        },
                        "region_attributes": {
                            "label": cls_name,
                            "confidence": conf
                        }
                    })

            self.via_export[img_id] = {
                "filename": im,
                "size": file_size,
                "regions": regions,
                "file_attributes": {}
            }

    def save_csv(self, filename="results.csv"):
        """
        Γράφει CSV με headers EXACT:
        filename,file_size,file_attributes,region_count,region_id,region_shape_attributes,region_attributes

        - Ένα row ανά region (αν δεν υπάρχουν regions, γράφει 1 γραμμή με κενά attributes και region_id="")
        - Τα *_attributes είναι JSON strings (π.χ. {"name":"rect","x":...})
        """
        out_path = os.path.join(self.out_dir, filename)

        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # ΑΚΡΙΒΩΣ αυτό το header
            writer.writerow([
                "filename",
                "file_size",
                "file_attributes",
                "region_count",
                "region_id",
                "region_shape_attributes",
                "region_attributes"
            ])

            for img_id, data in self.via_export.items():
                filename = data.get("filename", img_id)
                file_size = data.get("size", "")
                file_attributes = data.get("file_attributes", {})
                regions = data.get("regions", [])
                region_count = len(regions)

                # Αν δεν υπάρχουν regions: το VIA δέχεται κενή γραμμή με region_id κενό
                if region_count == 0:
                    writer.writerow([
                        filename,
                        file_size,
                        json.dumps(file_attributes, ensure_ascii=False),
                        0,
                        "",  # no region_id
                        json.dumps({}, ensure_ascii=False),
                        json.dumps({}, ensure_ascii=False)
                    ])
                    continue

                # Κανονικά: ένα row ανά region
                for ridx, region in enumerate(regions):
                    shape_attributes = region.get("shape_attributes", {})
                    region_attributes = region.get("region_attributes", {})

                    # Βεβαιώσου ότι το shape έχει "name":"rect" και integer x,y,width,height
                    # (τα έχεις ήδη δημιουργήσει σωστά στο via_export)
                    writer.writerow([
                        filename,
                        file_size,
                        json.dumps(file_attributes, ensure_ascii=False),
                        region_count,
                        ridx,  # 0-based
                        json.dumps(shape_attributes, ensure_ascii=False),
                        json.dumps(region_attributes, ensure_ascii=False)
                    ])

        print(f"✅ VIA CSV saved to: {out_path}")
        return out_path
