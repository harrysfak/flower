import zipfile
from tqdm import tqdm
import os

class Unziper:
    def __init__(self, file_path, out_dir="unzipped"):
        self.path = file_path
        self.out_dir = out_dir
        os.makedirs(out_dir, exist_ok=True)

    def unzip(self):
        with zipfile.ZipFile(self.path, "r") as z:
            members = z.infolist()   # λίστα αρχείων στο zip

            for member in tqdm(members, desc="Unzipping", unit="file"):
                z.extract(member, self.out_dir)
