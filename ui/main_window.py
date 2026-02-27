from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QFileDialog, QToolBar, QPushButton,
    QDockWidget, QComboBox, QLabel, QWidgetAction,
    QSizePolicy, QLineEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut, QKeySequence

from ui.gallery_widget import GalleryWidget
from ui.preview_panel import PreviewPanel
from ui.folder_panel import FolderPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dataset Manager v2")
        self.resize(1700, 900)

        self.setStyleSheet("""
        QMainWindow { background-color: #1e1e1e; }
        QLabel { color: white; font-size: 14px; }
        QComboBox { background-color: #2b2b2b; color: white; padding: 4px; }
        QListWidget { background-color: #1e1e1e; color: white; }
        QToolBar { background-color: #2b2b2b; spacing: 10px; }
        QPushButton { background-color: #3a3a3a; color: white; padding: 5px; }
        """)

        self.gallery = GalleryWidget()
        self.preview = PreviewPanel()
        self.folder_panel = FolderPanel()

        self.gallery.image_selected.connect(self.preview.load_image)
        self.preview.rating_callback = self.gallery.set_rating_for_selected
        self.folder_panel.folders_changed.connect(
            self.gallery.filter_by_folders
        )
        
        # NEW
        self.gallery.list_widget.model().rowsInserted.connect(self.update_image_count)
        self.gallery.list_widget.model().rowsRemoved.connect(self.update_image_count)

        # ⭐ Rating shortcuts 1-5
        for i in range(1, 6):
            shortcut = QShortcut(QKeySequence(str(i)), self)
            shortcut.activated.connect(lambda r=i: self.gallery.set_rating_for_selected(r))

        # --- Main Layout ---
        central = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)

        main_layout.addWidget(self.gallery, 5)
        main_layout.addWidget(self.preview, 2)

        central.setLayout(main_layout)
        self.setCentralWidget(central)

        # --- Left Dock (Subfolder Filter) ---
        self.dock = QDockWidget("Subfolders", self)
        self.dock.setWidget(self.folder_panel)

        # Important: remove closable so it never disappears permanently
        self.dock.setFeatures(QDockWidget.DockWidgetMovable)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock)

        self.create_toolbar()

    def create_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # LEFT SIDE
        open_btn = QPushButton("Open Dataset")
        open_btn.clicked.connect(self.open_folder)
        toolbar.addWidget(open_btn)

        toggle_btn = QPushButton("Toggle Subfolders")
        toggle_btn.clicked.connect(self.toggle_dock)
        toolbar.addWidget(toggle_btn)

        # Spacer pushes everything after this to right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)

        # RIGHT SIDE (like Stability Matrix)
        # sort image
        toolbar.addWidget(QLabel("Sort:"))

        self.sort_dropdown = QComboBox()
        self.sort_dropdown.addItems([
            "Name A-Z",
            "Name Z-A",
            "Resolution High → Low",
            "Resolution Low → High"
        ])
        toolbar.addWidget(self.sort_dropdown)
        self.sort_dropdown.currentTextChanged.connect(
            self.gallery.sort_images
        )
        
        toolbar.addSeparator()
        # size dropdown
        toolbar.addWidget(QLabel("Size"))

        self.size_dropdown = QComboBox()
        self.size_dropdown.addItems([
            "Any",
            "Small (<512)",
            "Medium (512–1024)",
            "Large (>1024)",
            "At least..."
        ])
        toolbar.addWidget(self.size_dropdown)

        self.min_width_label = QLabel("W:")
        self.min_width_label.hide()
        toolbar.addWidget(self.min_width_label)

        self.min_width_input = QLineEdit()
        self.min_width_input.setFixedWidth(70)
        self.min_width_input.hide()
        toolbar.addWidget(self.min_width_input)

        self.min_height_label = QLabel("H:")
        self.min_height_label.hide()
        toolbar.addWidget(self.min_height_label)

        self.min_height_input = QLineEdit()
        self.min_height_input.setFixedWidth(70)
        self.min_height_input.hide()
        toolbar.addWidget(self.min_height_input)

        self.size_dropdown.currentTextChanged.connect(
            self.handle_size_mode
        )

        self.min_width_input.editingFinished.connect(self.apply_size_filter)
        self.min_height_input.editingFinished.connect(self.apply_size_filter)

        toolbar.addSeparator()
        
        # image count
        self.image_count_label = QLabel("Images: 0")
        toolbar.addWidget(self.image_count_label)

    def toggle_dock(self):
        self.dock.setVisible(not self.dock.isVisible())

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Dataset Folder")
        if folder:
            self.gallery.load_folder(folder)
            self.folder_panel.load_subfolders(folder)

    def handle_size_mode(self, text):
        if text == "At least...":
            self.min_width_label.show()
            self.min_width_input.show()
            self.min_height_label.show()
            self.min_height_input.show()
        else:
            self.min_width_label.hide()
            self.min_width_input.hide()
            self.min_height_label.hide()
            self.min_height_input.hide()
            self.apply_size_filter()


    def apply_size_filter(self):
        mode = self.size_dropdown.currentText()

        if mode == "Any":
            self.gallery.set_size_filter(None)

        elif mode == "Small (<512)":
            self.gallery.set_size_filter((0, 512))

        elif mode == "Medium (512–1024)":
            self.gallery.set_size_filter((512, 1024))

        elif mode == "Large (>1024)":
            self.gallery.set_size_filter((1024, 99999))

        elif mode == "At least...":
            try:
                w = int(self.min_width_input.text())
                h = int(self.min_height_input.text())
                if w > 0 and h > 0:
                    self.gallery.set_min_dimensions(w, h)
            except:
                pass

    def update_image_count(self):
        count = self.gallery.list_widget.count()
        self.image_count_label.setText(f"Images: {count}")