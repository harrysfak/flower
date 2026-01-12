"""
Class for requesting /detect to server
"""

import requests
class Detector:
    def __init__(self, url="http://127.0.0.1:8000/detect"):
        self.url = url

    def run(self):
        try:
            resp = requests.post(self.url, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                return True, data
            else:
                return False, resp.text
        except Exception as e:
            return False, str(e)

