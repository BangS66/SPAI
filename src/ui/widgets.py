
from PySide6.QtWidgets import QPushButton, QFrame, QDialog, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt

class Colors:
    PRIMARY, SECONDARY, BACKGROUND, ACCENT, TEXT_DARK, CARD_BG = "#4A90E2", "#2D3E50", "#F7F9FC", "#50E3C2", "#1A1A1A", "#FFFFFF"

class ModernButton(QPushButton):
    def __init__(self, text, icon_text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"background-color: {Colors.PRIMARY}; color: white; border: none; border-radius: 8px; padding: 12px 24px; font-size: 14px; font-weight: 600;")

class SidebarButton(QPushButton):
    def __init__(self, text, icon_text="", parent=None):
        super().__init__(f"{icon_text}  {text}", parent)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("background-color: transparent; color: white; border: none; border-radius: 8px; padding: 12px 20px; font-size: 14px; text-align: left; margin: 4px 8px;")

class ModernCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {Colors.CARD_BG}; border-radius: 12px; border: 1px solid #E5E9F2;")

class ConfirmDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirm Action")
        self.operation = None
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Do you want to copy or move the files?"))
        btn_layout = QHBoxLayout()
        copy_btn, move_btn, cancel_btn = ModernButton("Copy"), ModernButton("Move"), QPushButton("Cancel")
        copy_btn.clicked.connect(lambda: self.done_action('copy'))
        move_btn.clicked.connect(lambda: self.done_action('move'))
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(copy_btn)
        btn_layout.addWidget(move_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def done_action(self, op):
        self.operation = op
        self.accept()
