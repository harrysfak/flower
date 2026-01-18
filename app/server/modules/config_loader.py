
import json
from pathlib import Path
from typing import Optional, Any

def find_cfg(start: Path, rel: str = "assets/cfg.json") -> Path:
    """
    Ψάχνει προς τα πάνω (parents) για έναν φάκελο που περιέχει rel (assets/cfg.json).
    Επιστρέφει το πρώτο που θα βρει, αλλιώς σηκώνει FileNotFoundError.
    """
    for base in [start] + list(start.parents):
        candidate = base / rel
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"Δεν βρέθηκε το {rel} ξεκινώντας από: {start}")

class ConfigLoader:
    def __init__(self, key: str, config_path: Optional[Path] = None):
        self.key = key
        # Αν δεν δοθεί config_path, προσπαθούμε να βρούμε το assets/cfg.json
        self.config_path = config_path or find_cfg(Path(__file__).resolve())

    def load_value(self, default: Any = None) -> Any:
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Δεν βρέθηκε το cfg.json στο: {self.config_path}") from e
        except json.JSONDecodeError as e:
            raise ValueError(f"To cfg.json δεν είναι έγκυρο JSON: {self.config_path}") from e

        if self.key in cfg:
            return cfg[self.key]
        if default is not None:
            return default
        raise KeyError(f"To key '{self.key}' δεν υπάρχει στο cfg.json")
