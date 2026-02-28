import json
from pathlib import Path


class SettingsManager:
    def __init__(self):
        self.settings_path = Path("settings.json")
        self.settings = self.load_settings()

    def load_settings(self):
        if self.settings_path.exists():
            try:
                with open(self.settings_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass

        # Default settings
        return {
            "dataset_base_path": ""
        }

    def save_settings(self):
        with open(self.settings_path, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=4)

    def get_dataset_base_path(self):
        return self.settings.get("dataset_base_path", "")

    def set_dataset_base_path(self, path):
        self.settings["dataset_base_path"] = path
        self.save_settings()