import psutil
from tqdm import tqdm
from ultralytics import YOLO
import os

from cpu_check import CPU_LIMIT, CPULimitExceeded


class Modelo():

    def __init__(self, image_dir, modelo="best.pt", out_dir="model_results"):
        if not os.path.exists(modelo):
            raise FileNotFoundError(f"Model not found: {modelo}")
        print(f"Corrected model path found: {modelo}")
        self.model = YOLO(modelo)
        print("YOLOv8 model loaded successfully.")


        self.image_dir = image_dir
        if not os.path.isdir(self.image_dir):
            raise NotADirectoryError(f"Image dir not found: {self.image_dir}")

        self.out_dir = out_dir
        os.makedirs(out_dir, exist_ok=True)

        self.results = {}

        exts = (".jpg", ".jpeg", ".png")
        self.list_of_img = [f for f in os.listdir(self.image_dir) if f.lower().endswith(exts)]

    def run_and_dictionarily_write(self, progress_callback=None):
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

            preds = self.model.predict(image_path, verbose=False)
            r0 = preds[0]
            boxes = r0.boxes
            n_bx = len(boxes) if boxes is not None else 0

            self.results[f"{im}"] = f"Detections : {n_bx}"
            if progress_callback:
                progress_callback(current=idx, total=total)

    def save_txt(self, filename="resD.txt"):
        out_path = os.path.join(self.out_dir, filename)

        # tqdm για πρόοδο στο γράψιμο
        with open(out_path, "w", encoding="utf-8") as f:
            for img_name, summary in tqdm(self.results.items(), desc="Saving", unit="img"):
                f.write(f"{img_name}: {summary}\n")

        return out_path
