from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout,
    QHBoxLayout, QPushButton
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from PIL import Image


class PreviewPanel(QWidget):
    def __init__(self):
        super().__init__()

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)

        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignTop)
        self.info_label.setStyleSheet("font-size: 15px;")

        layout = QVBoxLayout()
        layout.addWidget(self.image_label, 5)
        layout.addWidget(self.info_label, 1)

        self.setLayout(layout)

        self.star_layout = QHBoxLayout()
        self.star_buttons = []

        for i in range(1, 6):
            btn = QPushButton("☆")
            btn.setStyleSheet("font-size: 24px; color: gold; background: transparent; border: none;")
            btn.clicked.connect(lambda checked, r=i: self.set_rating(r))
            self.star_layout.addWidget(btn)
            self.star_buttons.append(btn)

        layout.addLayout(self.star_layout)

    def load_image(self, data):
        image_path, rating = data
        self.current_rating = rating
        self.update_stars()
        pixmap = QPixmap(image_path)

        self.image_label.setPixmap(
            pixmap.scaled(
                700,
                800,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )

        img = Image.open(image_path)
        width, height = img.size

        self.info_label.setText(
            f"Path: {image_path}\n"
            f"Resolution: {width} x {height}\n"
            f"Rating: {rating}"
        )
    
    def set_rating(self, rating):
        self.current_rating = rating
        self.update_stars()
        if hasattr(self, "rating_callback"):
            self.rating_callback(rating)

    def update_stars(self):
        for i, btn in enumerate(self.star_buttons, start=1):
            btn.setText("★" if i <= self.current_rating else "☆")