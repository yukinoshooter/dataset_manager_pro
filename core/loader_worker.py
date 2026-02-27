from PySide6.QtCore import QThread, Signal
from pathlib import Path
from PIL import Image
from core.image_loader import scan_images


class ImageLoaderWorker(QThread):
    finished_loading = Signal(list)

    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path

    def run(self):
        images_data = []
        root = Path(self.folder_path)

        image_paths = scan_images(self.folder_path)

        for img_path in image_paths:
            try:
                img = Image.open(img_path)
                width, height = img.size

                parent_path = Path(img_path).parent
                depth = len(parent_path.relative_to(root).parts)

                images_data.append({
                    "path": str(img_path),
                    "folder": str(parent_path),
                    "name": Path(img_path).name,
                    "width": width,
                    "height": height,
                    "resolution": width * height,
                    "rating": 0   # ⭐ default rating
                })
            except:
                continue

        self.finished_loading.emit(images_data)