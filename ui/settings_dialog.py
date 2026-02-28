from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QFileDialog,
    QHBoxLayout
)
from PySide6.QtCore import Qt


class SettingsDialog(QDialog):
    def __init__(self, settings_manager):
        super().__init__()
        self.setWindowTitle("Settings")
        self.setFixedWidth(500)

        self.settings_manager = settings_manager

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Dataset Base Path:"))

        path_layout = QHBoxLayout()

        self.path_input = QLineEdit()
        self.path_input.setText(
            self.settings_manager.get_dataset_base_path()
        )

        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_folder)

        path_layout.addWidget(self.path_input)
        path_layout.addWidget(browse_btn)

        layout.addLayout(path_layout)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)

        self.setLayout(layout)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Dataset Base Folder"
        )
        if folder:
            self.path_input.setText(folder)

    def save_settings(self):
        self.settings_manager.set_dataset_base_path(
            self.path_input.text()
        )
        self.accept()