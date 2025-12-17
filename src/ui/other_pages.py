
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout, QFileDialog
from PySide6.QtCore import Qt
from ui.widgets import ModernCard, ModernButton
import os

class AboutPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        card = ModernCard()
        card.setMaximumWidth(500)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(15)
        card_layout.setAlignment(Qt.AlignCenter)

        logo = QLabel("🎨")
        logo.setStyleSheet("font-size: 64px;")

        app_name = QLabel("SPAI")
        app_name.setStyleSheet("font-size: 32px; font-weight: 700; color: #4A90E2;")

        desc = QLabel("Smart Photo AI")
        desc.setStyleSheet("font-size: 16px; color: #7F8C9A;")

        version = QLabel("Version 1.0.0")

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)

        creator_layout = QHBoxLayout()
        creator_layout.setAlignment(Qt.AlignCenter)
        creator_layout.addWidget(QLabel("Created by:"))
        creator_layout.addWidget(QLabel("📷"))
        creator_layout.addWidget(QLabel("@wawansft"))

        card_layout.addWidget(logo, 0, Qt.AlignCenter)
        card_layout.addWidget(app_name, 0, Qt.AlignCenter)
        card_layout.addWidget(desc, 0, Qt.AlignCenter)
        card_layout.addWidget(version, 0, Qt.AlignCenter)
        card_layout.addWidget(separator)
        card_layout.addLayout(creator_layout)

        layout.addWidget(card)

class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.output_folder = os.path.expanduser("~")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("⚙️ Settings", styleSheet="font-size: 28px; font-weight: 700;"))
        folder_card = ModernCard()
        folder_layout = QVBoxLayout(folder_card)
        self.current_folder_label = QLabel(f"Current Output Folder: {self.output_folder}")
        change_folder_btn = ModernButton("Change Folder")
        change_folder_btn.clicked.connect(self.change_folder)
        folder_layout.addWidget(self.current_folder_label)
        folder_layout.addWidget(change_folder_btn)
        layout.addWidget(folder_card)
        layout.addStretch()

    def change_folder(self):
        if folder := QFileDialog.getExistingDirectory(self, "Select Folder"):
            self.output_folder = folder
            self.current_folder_label.setText(f"Current Output Folder: {self.output_folder}")
