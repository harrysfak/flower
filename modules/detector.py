
"""
Class for requesting to server
"""

import os
import re
import requests

class ApiCaller:
    def __init__(self, base_url="http://127.0.0.1:5000"):
        self.base_url = base_url.rstrip("/")
        self.detection_url = f"{self.base_url}/detect"
        self.download_url  = f"{self.base_url}/download"
        # Πού θα το αποθηκεύσεις τοπικά (προσαρμοσέ το αν θες)
        self.local_results_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "model_results"))
        os.makedirs(self.local_results_dir, exist_ok=True)

    def run(self):
        try:
            resp = requests.post(self.detection_url, timeout=60)
            if resp.status_code == 200:
                # Αν επιστρέφεις JSON από το /detect
                data = resp.json()
                return True, data
            else:
                return False, resp.text
        except Exception as e:
            return False, str(e)

    def _filename_from_content_disposition(self, cd_header, default_name="via_export_csv.csv"):
        """
        Εξάγει filename από Content-Disposition (αν υπάρχει).
        Παράδειγμα header: 'attachment; filename="via_export_csv.csv"'
        """
        if not cd_header:
            return default_name
        # Προσπάθεια για filename* (RFC 5987) — σπάνιο αλλά καλό να υπάρχει
        m_star = re.search(r'filename\*\s*=\s*[^\'"]*\'\'(?P<fn>[^;]+)', cd_header)
        if m_star:
            return m_star.group("fn")
        # Κλασικό filename=
        m = re.search(r'filename\s*=\s*"?(?P<fn>[^";]+)"?', cd_header)
        if m:
            return m.group("fn")
        return default_name

    def download(self, timeout=60, default_name="via_export_csv.csv"):
        """
        Κατεβάζει το CSV από /download και το αποθηκεύει στο self.local_results_dir.
        Επιστρέφει: (True, saved_path) ή (False, error_msg)
        """
        try:
            with requests.get(self.download_url, stream=True, timeout=timeout) as resp:
                if resp.status_code != 200:
                    return False, f"Download failed: HTTP {resp.status_code}"

                # Πάρε το filename από το Content-Disposition αν υπάρχει
                cd = resp.headers.get("Content-Disposition", "")
                filename = self._filename_from_content_disposition(cd, default_name=default_name)

                # Ασφαλής καθαρισμός ονόματος αρχείου
                filename = os.path.basename(filename)
                if not filename.lower().endswith(".csv"):
                    # Εξασφάλισε .csv επέκταση
                    filename += ".csv"

                saved_path = os.path.join(self.local_results_dir, filename)

                # Γράψε το αρχείο σε chunks
                with open(saved_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:  # filter out keep-alive chunks
                            f.write(chunk)

                return True, saved_path

        except Exception as e:
            return False, str(e)
