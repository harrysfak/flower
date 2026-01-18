"""
Class for loading configuration from cfg.json
"""
import json

CONFIG_PATH = r"assets\cfg.json"


class ConfigLoader:

    def __init__(self, key):
        self.cfg_path = CONFIG_PATH
        self.key = key

    def load_value(self):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        return cfg[self.key]
