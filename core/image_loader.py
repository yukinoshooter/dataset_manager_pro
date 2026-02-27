from pathlib import Path

SUPPORTED_FORMATS = [".png", ".jpg", ".jpeg", ".webp"]


def scan_images(folder_path):
    folder = Path(folder_path)
    images = []

    def scan_directory(directory):
        # 1️⃣ Add images in this directory first
        for file in sorted(directory.iterdir()):
            if file.is_file() and file.suffix.lower() in SUPPORTED_FORMATS:
                images.append(file)

        # 2️⃣ Then scan subdirectories
        for sub in sorted(directory.iterdir()):
            if sub.is_dir():
                scan_directory(sub)

    scan_directory(folder)

    return images