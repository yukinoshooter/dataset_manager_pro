from PySide6.QtWidgets import (
    QWidget, QListWidget, QListWidgetItem,
    QVBoxLayout
)
from PySide6.QtCore import Signal, QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from pathlib import Path
from PIL import Image
from PIL.ImageQt import ImageQt
from core.loader_worker import ImageLoaderWorker
from core.metadata_manager import MetadataManager

class GalleryWidget(QWidget):
    image_selected = Signal(object)

    def __init__(self):
        super().__init__()

        self.root_path = None
        self.images_data = []
        self.filtered_data = []

        self.selected_folders = None
        self.rating_filter = None
        self.size_range = None
        self.min_width = None
        self.min_height = None

        self.thumbnail_cache = {}   # 🔥 cache added

        self.thumb_size = 260

        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.IconMode)
        self.list_widget.setMovement(QListWidget.Static)
        self.list_widget.setResizeMode(QListWidget.Adjust)
        self.list_widget.setSpacing(16)
        self.list_widget.setIconSize(QSize(self.thumb_size, self.thumb_size))
        self.list_widget.setGridSize(QSize(self.thumb_size + 30, self.thumb_size + 40))
        self.list_widget.setWrapping(True)

        self.list_widget.itemClicked.connect(self.on_item_clicked)
        self.list_widget.setSelectionMode(QListWidget.ExtendedSelection)

        layout = QVBoxLayout()
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

    # -----------------------------
    # Loading
    # -----------------------------

    def load_folder(self, folder_path):
        """
        Load dataset folder.
        Stops previous worker safely,
        resets image data,
        and initializes metadata manager.
        """
        self.root_path = Path(folder_path)

        # --- Stop previous worker safely ---
        if hasattr(self, "worker") and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()

        # --- Initialize metadata manager ---
        from core.settings_manager import SettingsManager

        settings = SettingsManager()
        dataset_base = settings.get_dataset_base_path()

        self.metadata = MetadataManager(folder_path, dataset_base)

        # --- Reset state ---
        self.images_data = []
        self.filtered_data = []
        self.thumbnail_cache.clear()
        self.display_images([])

        # --- Start background loader ---
        self.worker = ImageLoaderWorker(folder_path)
        self.worker.finished_loading.connect(self.on_loading_finished)
        self.worker.start()

    def on_loading_finished(self, images_data):
        self.images_data = images_data

        # Load saved ratings
        for img in self.images_data:
            relative_path = str(
                Path(img["path"]).relative_to(self.root_path)
            ).replace("\\", "/")

            img["rating"] = self.metadata.get_rating(relative_path)

         # Clean invalid rating entries
        valid_paths = [
            str(Path(img["path"]).relative_to(self.root_path)).replace("\\", "/")
            for img in self.images_data
        ]
        self.metadata.clean_orphan_entries(valid_paths)
        
        self.apply_filters()

    # -----------------------------
    # Filtering
    # -----------------------------

    def filter_by_folders(self, selected_folders):
        self.selected_folders = selected_folders or []
        self.apply_filters()

    def set_size_filter(self, size_range):
        self.size_range = size_range
        self.min_width = None
        self.min_height = None
        self.apply_filters()

    def set_min_dimensions(self, width, height):
        self.min_width = width
        self.min_height = height
        self.size_range = None
        self.apply_filters()

    def apply_filters(self):
        data = self.images_data

        # Folder filter
        if self.selected_folders is not None:
            if len(self.selected_folders) == 0:
                data = []  # user unchecked all → show nothing
            else:
                data = [
                    img for img in data
                    if img["folder"] in self.selected_folders
                ]

        # Size range filter (based on max dimension)
        if self.size_range:
            min_val, max_val = self.size_range
            data = [
                img for img in data
                if min_val <= max(img["width"], img["height"]) <= max_val
            ]

        # Minimum width/height filter
        if self.min_width and self.min_height:
            data = [
                img for img in data
                if img["width"] >= self.min_width
                and img["height"] >= self.min_height
            ]

        # Rating filter
        if self.rating_filter is not None:
            data = [
                img for img in data
                if img.get("rating", 0) in self.rating_filter
            ]

        self.filtered_data = data
        self.display_images(self.filtered_data)

    # -----------------------------
    # Display (with cache)
    # -----------------------------

    def display_images(self, images):
        self.list_widget.clear()

        for data in images:
            path = data["path"]

            if path in self.thumbnail_cache:
                pixmap = self.thumbnail_cache[path]
            else:
                try:
                    img = Image.open(path)
                    img.thumbnail((self.thumb_size, self.thumb_size))
                    qt_image = ImageQt(img)
                    pixmap = QPixmap.fromImage(qt_image)
                    self.thumbnail_cache[path] = pixmap
                except:
                    continue

            # draw rating overlay
            rating = data.get("rating", 0)

            if rating > 0:
                from PySide6.QtGui import QPainter, QColor, QFont

                pix = QPixmap(pixmap)
                painter = QPainter(pix)
                painter.setPen(QColor("yellow"))
                painter.setFont(QFont("Arial", 20, QFont.Bold))
                painter.drawText(10, 30, f"{rating}★")
                painter.end()

                icon = QIcon(pix)
            else:
                icon = QIcon(pixmap)

            item = QListWidgetItem()
            item.setIcon(icon)
            item.setData(Qt.UserRole, path)
            item.setSizeHint(QSize(self.thumb_size + 20, self.thumb_size + 20))

            self.list_widget.addItem(item)

    # -----------------------------
    # Rating System
    # -----------------------------
    
    def set_rating_for_selected(self, rating):
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            return

        for item in selected_items:
            path = Path(item.data(Qt.UserRole))

            # 🔥 relative path inside current root
            relative_path = str(Path(path).relative_to(self.root_path)).replace("\\", "/")

            # Update image_data
            for img in self.images_data:
                if img["path"] == str(path):
                    img["rating"] = rating
                    break

            self.metadata.set_rating(relative_path, rating)

        self.apply_filters()

    def set_rating_filter(self, ratings):
        self.rating_filter = ratings
        self.apply_filters()

    # -----------------------------
    # Sorting
    # -----------------------------

    def sort_images(self, mode):
        if mode == "Name A-Z":
            self.filtered_data.sort(key=lambda x: x["name"])
        elif mode == "Name Z-A":
            self.filtered_data.sort(key=lambda x: x["name"], reverse=True)
        elif mode == "Resolution High → Low":
            self.filtered_data.sort(key=lambda x: x["resolution"], reverse=True)
        elif mode == "Resolution Low → High":
            self.filtered_data.sort(key=lambda x: x["resolution"])

        self.display_images(self.filtered_data)

    # -----------------------------
    # Click
    # -----------------------------

    def on_item_clicked(self, item):
        path = item.data(Qt.UserRole)
        for img in self.images_data:
            if img["path"] == path:
                rating = img.get("rating", 0)
                break
        else:
            rating = 0

        self.image_selected.emit((path, rating))