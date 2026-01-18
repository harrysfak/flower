"""
Class for file sending via request
"""
import requests
import os


class FileSender:
    def __init__(self, url, filepath):
        self.url = url
        self.filepath = filepath

    def send_file(self):
        try:
            with open(self.filepath, "rb") as f:
                files = {
                    "the_file": (os.path.basename(self.filepath), f, "application/zip")
                }
                resp = requests.post(self.url, files=files, timeout=15)

            if resp.status_code == 200:
                return True, resp.text
            else:
                return False, f"Server error: {resp.status_code}"

        except Exception as e:
            return False, str(e)
