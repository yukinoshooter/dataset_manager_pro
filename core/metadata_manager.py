import json
from pathlib import Path


class MetadataManager:
    """
    Image-driven metadata manager.

    - Supports dataset base architecture
    - Uses first-level subfolder rule
    - Chooses metadata file based on image relative path
    - Caches multiple metadata files in memory
    """

    def __init__(self, current_folder, dataset_base_path=None):
        self.current_folder = Path(current_folder)
        self.dataset_base = (
            Path(dataset_base_path)
            if dataset_base_path else None
        )

        self.dataset_name = None
        self.metadata_root = None

        self.metadata_cache = {}  # {metadata_path: ratings_dict}

        self.initialize_dataset_context()

    # ---------------------------------------------------------
    # Dataset Context Setup
    # ---------------------------------------------------------

    def initialize_dataset_context(self):
        """
        Determine dataset name and metadata root directory.
        """

        if (
            self.dataset_base
            and self.current_folder.is_relative_to(self.dataset_base)
        ):
            relative = self.current_folder.relative_to(self.dataset_base)
            parts = relative.parts

            if len(parts) == 0:
                self.dataset_name = self.current_folder.name
            else:
                self.dataset_name = parts[0]

            self.metadata_root = (
                self.dataset_base / "_metadata" / self.dataset_name
            )
            self.metadata_root.mkdir(parents=True, exist_ok=True)

        else:
            # Outside dataset base → fallback local metadata
            self.dataset_name = None
            self.metadata_root = self.current_folder

    # ---------------------------------------------------------
    # Metadata File Resolver (IMAGE-DRIVEN)
    # ---------------------------------------------------------

    def resolve_metadata_file(self, relative_path):
        """
        Decide which metadata file to use based on image path.
        """

        if not self.dataset_name:
            # Fallback local metadata
            return self.metadata_root / ".ratings.json"

        parts = Path(relative_path).parts

        if len(parts) == 1:
            # Image in dataset root
            return self.metadata_root / "ratings.json"
        else:
            # Image in first-level subfolder
            first_subfolder = parts[0]
            return self.metadata_root / f"{first_subfolder}-ratings.json"

    # ---------------------------------------------------------
    # Load Metadata File
    # ---------------------------------------------------------

    def load_metadata_file(self, metadata_file):
        if metadata_file in self.metadata_cache:
            return self.metadata_cache[metadata_file]

        if metadata_file.exists():
            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except:
                data = {}
        else:
            data = {}

        self.metadata_cache[metadata_file] = data
        return data

    def save_metadata_file(self, metadata_file):
        data = self.metadata_cache.get(metadata_file, {})

        # 🔥 Ensure parent directory exists
        metadata_file.parent.mkdir(parents=True, exist_ok=True)

        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    # ---------------------------------------------------------
    # Public Rating API
    # ---------------------------------------------------------

    def get_rating(self, relative_path):
        metadata_file = self.resolve_metadata_file(relative_path)
        data = self.load_metadata_file(metadata_file)
        return data.get(relative_path, 0)

    def set_rating(self, relative_path, rating):
        metadata_file = self.resolve_metadata_file(relative_path)
        data = self.load_metadata_file(metadata_file)

        if rating == 0:
            data.pop(relative_path, None)
        else:
            data[relative_path] = rating

        self.save_metadata_file(metadata_file)

    # ---------------------------------------------------------
    # Cleanup Orphan Entries
    # ---------------------------------------------------------

    def clean_orphan_entries(self, valid_relative_paths):
        valid_set = set(valid_relative_paths)

        for metadata_file, data in self.metadata_cache.items():
            removed = False
            for key in list(data.keys()):
                if key not in valid_set:
                    data.pop(key)
                    removed = True

            if removed:
                self.save_metadata_file(metadata_file)