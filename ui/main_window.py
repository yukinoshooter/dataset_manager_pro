from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QFileDialog, QToolBar, QPushButton,
    QDockWidget, QComboBox, QLabel, QWidgetAction,
    QSizePolicy, QLineEdit, QToolButton, QMenu,
    QCheckBox, QInputDialog, QMessageBox
)
from PySide6.QtGui import QIcon
import shutil
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut, QKeySequence
from send2trash import send2trash

from core.settings_manager import SettingsManager
from ui.settings_dialog import SettingsDialog
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
        QToolButton { background-color: #3a3a3a; color: white; padding: 5px; }

        QMessageBox {
            background-color: #f0f0f0;
        }
        QMessageBox QLabel {
            color: black;
        }

        QInputDialog {
            background-color: #f0f0f0;
        }
        QInputDialog QLabel {
            color: black;
        }
        QInputDialog QLineEdit {
            background-color: white;
            color: black;
        }
        """)
        
        self.settings_manager = SettingsManager()
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
        self.add_settings_button()

        base_path = self.settings_manager.get_dataset_base_path()

        if not base_path:
            self.open_settings_dialog()
            base_path = self.settings_manager.get_dataset_base_path()

        if not base_path:
            QMessageBox.critical(
                self,
                "Dataset Base Required",
                "Dataset Base must be set to use this app."
            )
            self.close()
            return

        self.create_toolbar()
        self.load_dataset_list()

    def create_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # LEFT SIDE

        toggle_btn = QPushButton("T☰ Toggle")
        toggle_btn.clicked.connect(self.toggle_dock)
        toolbar.addWidget(toggle_btn)
        
        # Refresh Button
        self.refresh_btn = QToolButton()
        self.refresh_btn.setText("⟳")
        self.refresh_btn.setToolTip("Refresh Gallery")
        self.refresh_btn.clicked.connect(self.refresh_gallery)
        toolbar.addWidget(self.refresh_btn)

        #Dataset button
        toolbar.addWidget(QLabel("Dataset:"))

        self.dataset_dropdown = QComboBox()
        self.dataset_dropdown.currentTextChanged.connect(self.load_selected_dataset)
        toolbar.addWidget(self.dataset_dropdown)

        # Spacer pushes everything after this to right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)

        # RIGHT SIDE (like Stability Matrix)
        
        # Dataset Management
        # Select All
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self.select_all_images)
        toolbar.addWidget(self.select_all_btn)

        # Deselect All
        self.deselect_all_btn = QPushButton("Clear Selection")
        self.deselect_all_btn.clicked.connect(self.clear_selection)
        toolbar.addWidget(self.deselect_all_btn)

        # Move Selected
        self.move_selected_btn = QPushButton("Move Selected")
        self.move_selected_btn.clicked.connect(self.move_selected_images)
        toolbar.addWidget(self.move_selected_btn)

        toolbar.addSeparator()

        # Create Folder
        self.create_folder_btn = QPushButton("New Folder")
        self.create_folder_btn.clicked.connect(self.create_new_folder)
        toolbar.addWidget(self.create_folder_btn)

        # Delete Selected
        self.delete_selected_btn = QPushButton("Delete Selected")
        self.delete_selected_btn.clicked.connect(self.delete_selected_images)
        toolbar.addWidget(self.delete_selected_btn)
                
        # sort image
        toolbar.addSeparator()
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
        
        # size dropdown

        toolbar.addSeparator()
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

        # ---------- rating dropdown (checkbox menu) ----------
        toolbar.addSeparator()
        toolbar.addWidget(QLabel("Rating:"))

        self.rating_button = QToolButton()
        self.rating_button.setText("Any ▼")
        self.rating_button.setPopupMode(QToolButton.InstantPopup)

        self.rating_menu = QMenu(self)
        self.rating_checkboxes = {}

        # --- Any checkbox ---
        self.any_checkbox = QCheckBox("Any")
        self.any_checkbox.setChecked(True)
        self.any_checkbox.stateChanged.connect(self.handle_any_rating_toggle)

        any_action = QWidgetAction(self)
        any_action.setDefaultWidget(self.any_checkbox)
        self.rating_menu.addAction(any_action)

        self.rating_menu.addSeparator()

        # --- Rating checkboxes (0 = Unrated) ---
        for i in range(0, 6):
            text = "Unrated" if i == 0 else f"{i}★"
            checkbox = QCheckBox(text)
            checkbox.setChecked(True)  # default visible
            checkbox.stateChanged.connect(self.apply_rating_filter)

            action = QWidgetAction(self)
            action.setDefaultWidget(checkbox)
            self.rating_menu.addAction(action)

            self.rating_checkboxes[i] = checkbox

        # Save the *initial* selection snapshot so "Any" can restore it
        self._initial_rating_state = {r: cb.isChecked() for r, cb in self.rating_checkboxes.items()}

        self.rating_button.setMenu(self.rating_menu)
        toolbar.addWidget(self.rating_button)
        # ---------------------------------------------------

        # image count
        toolbar.addSeparator()
        self.image_count_label = QLabel("Images: 0")
        toolbar.addWidget(self.image_count_label)

    def add_settings_button(self):
        self.settings_button = QPushButton("⚙ Settings")
        self.settings_button.setFixedHeight(28)
        self.settings_button.clicked.connect(self.open_settings_dialog)

        # Place below dock title
        self.dock.setTitleBarWidget(QWidget())
        dock_layout = QVBoxLayout()
        dock_layout.setContentsMargins(4, 4, 4, 4)

        container = QWidget()
        dock_layout.addWidget(self.settings_button)
        dock_layout.addWidget(self.folder_panel)
        container.setLayout(dock_layout)

        self.dock.setWidget(container)

    def open_settings_dialog(self):
        dialog = SettingsDialog(self.settings_manager)
        dialog.exec()
    
    #Load Dataset
    def load_dataset_list(self):
        base_path = Path(self.settings_manager.get_dataset_base_path())

        datasets = [
            f.name for f in base_path.iterdir()
            if f.is_dir() and f.name != "_metadata"
        ]

        self.dataset_dropdown.clear()
        self.dataset_dropdown.addItems(sorted(datasets))

    def load_selected_dataset(self, dataset_name):
        if not dataset_name:
            return

        base_path = Path(self.settings_manager.get_dataset_base_path())
        dataset_path = base_path / dataset_name

        self.gallery.load_folder(str(dataset_path))
        self.folder_panel.load_subfolders(str(dataset_path))
    
    #Refresh gallery
    def refresh_gallery(self):
        if self.gallery.root_path:
            self.gallery.load_folder(str(self.gallery.root_path))

    def toggle_dock(self):
        self.dock.setVisible(not self.dock.isVisible())

    # file management

    def select_all_images(self):
        self.gallery.list_widget.selectAll()

    def clear_selection(self):
        self.gallery.list_widget.clearSelection()

    def move_selected_images(self):
        selected_items = self.gallery.list_widget.selectedItems()

        if not selected_items:
            return

        # Ask for destination folder inside dataset
        dest_folder = QFileDialog.getExistingDirectory(
            self, "Select Destination Folder"
        )

        if not dest_folder:
            return

        dest_path = Path(dest_folder)

        for item in selected_items:
            src_path = Path(item.data(Qt.UserRole))
            try:
                shutil.move(str(src_path), str(dest_path / src_path.name))
            except Exception as e:
                print("Move failed:", e)

        # Reload gallery after move
        self.gallery.load_folder(str(self.gallery.root_path))

    def create_new_folder(self):
        if not self.gallery.root_path:
            return

        folder_name, ok = QInputDialog.getText(
            self,
            "Create New Folder",
            "Enter folder name:"
        )

        if not (ok and folder_name):
            return

        # 🔥 Determine selected folder in tree
        current_item = self.folder_panel.tree.currentItem()

        if current_item and current_item.data(0, Qt.UserRole):
            target_path = Path(current_item.data(0, Qt.UserRole))
        else:
            target_path = Path(self.gallery.root_path)

        new_path = target_path / folder_name

        try:
            new_path.mkdir(exist_ok=False)
        except FileExistsError:
            QMessageBox.warning(self, "Error", "Folder already exists.")
            return
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return

        # 🔥 Add new folder to tree without full reload
        self.folder_panel.add_folder_to_tree(str(new_path))

    def delete_selected_images(self):
        selected_items = self.gallery.list_widget.selectedItems()

        if not selected_items:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Send {len(selected_items)} selected image(s) to Recycle Bin?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        for item in selected_items:
            path = Path(item.data(Qt.UserRole))
            try:
                send2trash(str(path))
            except Exception as e:
                print("Delete failed:", e)

        # Reload gallery
        self.gallery.load_folder(str(self.gallery.root_path))
        
    #Filter

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
    
    def handle_any_rating_toggle(self, state):
        checked = state == Qt.Checked

        # Force all rating checkboxes to match "Any"
        for cb in self.rating_checkboxes.values():
            cb.blockSignals(True)
            cb.setChecked(checked)
            cb.blockSignals(False)

        # Apply filter
        if checked:
            self.rating_button.setText("Any ▼")
            self.gallery.set_rating_filter(None)
        else:
            self.rating_button.setText("None ▼")
            self.gallery.set_rating_filter([])


    def apply_rating_filter(self):
        selected = [r for r, cb in self.rating_checkboxes.items() if cb.isChecked()]
        total = len(self.rating_checkboxes)

        # Update "Any" automatically
        self.any_checkbox.blockSignals(True)

        if len(selected) == total:
            self.any_checkbox.setChecked(True)
            self.rating_button.setText("Any ▼")
            self.gallery.set_rating_filter(None)
        elif len(selected) == 0:
            self.any_checkbox.setChecked(False)
            self.rating_button.setText("None ▼")
            self.gallery.set_rating_filter([])
        else:
            self.any_checkbox.setChecked(False)
            self.rating_button.setText("Custom ▼")
            self.gallery.set_rating_filter(selected)

        self.any_checkbox.blockSignals(False)

    def update_image_count(self):
        count = self.gallery.list_widget.count()
        self.image_count_label.setText(f"Images: {count}")