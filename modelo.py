import psutil
from tqdm import tqdm
from ultralytics import YOLO
import os

from cpu_check import CPU_LIMIT, CPULimitExceeded
from modules.via_vgg_exporter import ViaVggExporter


class Modelo():

    def __init__(self, image_dir, modelo="best.pt", out_dir="model_results", conf_thres=0.25):
        if not os.path.exists(modelo):
            raise FileNotFoundError(f"Model not found: {modelo}")
        print(f"Corrected model path found: {modelo}")
        self.model = YOLO(modelo)
        print("YOLOv8 model loaded successfully.")

        self.image_dir = image_dir
        if not os.path.isdir(self.image_dir):
            raise NotADirectoryError(f"Image dir not found: {self.image_dir}")

        self.out_dir = out_dir
        self.conf_thres = conf_thres
        os.makedirs(out_dir, exist_ok=True)

        exts = (".jpg", ".jpeg", ".png")
        self.list_of_img = [f for f in os.listdir(self.image_dir) if f.lower().endswith(exts)]

        # results[filename] = {"count": int, "boxes": [{"x","y","w","h","conf","class_id"}]}
        self.results = {}

    def run_and_collect(self, progress_callback=None):
        total = len(self.list_of_img)
        if progress_callback:
            progress_callback(current=0, total=total)

        for idx, im in enumerate(tqdm(self.list_of_img, desc="Predicting", colour="green", unit="img"), start=1):
            #CPU CHECK
            cpu = psutil.cpu_percent(interval=0.2)
            if cpu > CPU_LIMIT:
                print(f"\n⛔ CPU {cpu}% exceeded → stopping early")
                raise CPULimitExceeded(f"CPU {cpu}% exceeded")

            image_path = os.path.join(self.image_dir, im)

            pred = self.model.predict(image_path, verbose=False)[0]
            boxes_out = []

            if pred.boxes is not None and len(pred.boxes) > 0:
                xyxy = pred.boxes.xyxy.cpu().tolist()
                confs = pred.boxes.conf.cpu().tolist() if pred.boxes.conf is not None else [None] * len(xyxy)
                clss = pred.boxes.cls.cpu().tolist() if pred.boxes.cls is not None else [None] * len(xyxy)

                for (x1, y1, x2, y2), conf, cls in zip(xyxy, confs, clss):
                    if conf is not None and conf < self.conf_thres:
                        continue
                    x, y, w, h = ViaVggExporter._xyxy_to_xywh(x1, y1, x2, y2)
                    boxes_out.append(
                        {
                            "x": x,
                            "y": y,
                            "w": w,
                            "h": h,
                            "conf": float(conf) if conf is not None else "",
                            "class_id": int(cls) if cls is not None else "",
                        }
                    )

            self.results[im] = {"count": len(boxes_out), "boxes": boxes_out}
            if progress_callback:
                progress_callback(current=idx, total=total)

    def run_and_dictionarily_write(self, progress_callback=None):
        self.run_and_collect(progress_callback=progress_callback)

    def save_txt(self, filename="resD.txt"):
        out_path = os.path.join(self.out_dir, filename)

        # tqdm για πρόοδο στο γράψιμο
        with open(out_path, "w", encoding="utf-8") as f:
            for img_name, summary in tqdm(self.results.items(), desc="Saving", unit="img"):
                count = summary.get("count", 0)
                f.write(f"{img_name}: Detections : {count}\n")

        return out_path

    def export_via_and_csv(self, json_name="via_region_data.json", csv_name="predictions.csv"):
        out_json = os.path.join(self.out_dir, json_name)
        out_csv = os.path.join(self.out_dir, csv_name)
        ViaVggExporter(self.image_dir).export(self.results, out_json, out_csv)
        return out_json, out_csv
