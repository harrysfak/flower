import csv
import json
import os
from pathlib import Path

from PIL import Image


class ViaVggExporter:
    """
    Exports predictions to VGG Image Annotator (VIA) 2.x format:
    - JSON: via_region_data.json (Project -> Import)
    - CSV: fallback (filename, x, y, width, height, class_id, confidence)
    """

    def __init__(self, image_dir: str):
        self.image_dir = image_dir

    @staticmethod
    def _xyxy_to_xywh(x1, y1, x2, y2):
        x = int(x1)
        y = int(y1)
        w = int(x2 - x1)
        h = int(y2 - y1)
        # clamp negatives just in case
        return max(x, 0), max(y, 0), max(w, 0), max(h, 0)

    def export(self, results: dict, out_json: str, out_csv: str):
        via = {
            "_via_settings": {},
            "_via_img_metadata": {},
            "_via_attributes": {"region": {}, "file": {}},
        }

        csv_rows = [["filename", "x", "y", "width", "height", "class_id", "confidence"]]

        for filename, data in results.items():
            img_path = os.path.join(self.image_dir, filename)
            if not os.path.exists(img_path):
                continue

            file_size = os.path.getsize(img_path)
            w_img, h_img = Image.open(img_path).size

            regions = []
            for box in data.get("boxes", []):
                x, y, ww, hh = int(box["x"]), int(box["y"]), int(box["w"]), int(box["h"])
                class_id = box.get("class_id", "")
                conf = box.get("conf", "")

                regions.append(
                    {
                        "shape_attributes": {
                            "name": "rect",
                            "x": x,
                            "y": y,
                            "width": ww,
                            "height": hh,
                        },
                        "region_attributes": {"class_id": class_id},
                    }
                )

                csv_rows.append([filename, x, y, ww, hh, class_id, conf])

            key = f"{filename}{file_size}"
            via["_via_img_metadata"][key] = {
                "filename": filename,
                "size": file_size,
                "width": w_img,
                "height": h_img,
                "regions": regions,
                "file_attributes": {},
            }

        os.makedirs(Path(out_json).parent or ".", exist_ok=True)
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(via, f, ensure_ascii=False)

        os.makedirs(Path(out_csv).parent or ".", exist_ok=True)
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(csv_rows)
