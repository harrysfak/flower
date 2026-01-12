import zipfile
from tqdm import tqdm
import os

class Unziper:
    def __init__(self, file_path, out_dir="unzipped", progress_callback=None):
        self.path = file_path
        self.out_dir = out_dir
        self.progress_callback = progress_callback
        os.makedirs(out_dir, exist_ok=True)

    def unzip(self):
        with zipfile.ZipFile(self.path, "r") as z:
            members = z.infolist()   # λίστα αρχείων στο zip
            total = len(members)
            if self.progress_callback:
                self.progress_callback(current=0, total=total)

            for idx, member in enumerate(tqdm(members, desc="Unzipping", unit="file"), start=1):
                z.extract(member, self.out_dir)
                if self.progress_callback:
                    self.progress_callback(current=idx, total=total)
