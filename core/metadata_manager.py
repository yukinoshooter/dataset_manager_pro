import json
from pathlib import Path


class MetadataManager:
    def __init__(self, dataset_root):
        self.dataset_root = Path(dataset_root)
        self.metadata_path = self.dataset_root / "ratings.json"
        self.data = {}
        self.load()

    def load(self):
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except:
                self.data = {}
        else:
            self.data = {}

    def save(self):
        with open(self.metadata_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4)

    def get_rating(self, image_name):
        return self.data.get(image_name, 0)

    def set_rating(self, image_name, rating):
        self.data[image_name] = rating
        self.save()