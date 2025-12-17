
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, QGridLayout, QProgressBar
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap

from ui.widgets import ModernButton, ModernCard
from backend.workers import AnalysisWorker

class DragDropArea(QFrame):
    folder_selected = Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setStyleSheet(f"background-color: #F0F0F0; border: 2px dashed #4A90E2; border-radius: 12px;")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(QLabel("📁", alignment=Qt.AlignCenter), 0, Qt.AlignCenter)
        layout.addWidget(QLabel("Drag & Drop Folder Here", alignment=Qt.AlignCenter), 0, Qt.AlignCenter)
        browse_btn = ModernButton("Browse Folder")
        browse_btn.clicked.connect(self.browse_folder)
        layout.addWidget(browse_btn, 0, Qt.AlignCenter)

    def dragEnterEvent(self, event): event.acceptProposedAction() if event.mimeData().hasUrls() else event.ignore()
    def dropEvent(self, event):
        if url := next((url for url in event.mimeData().urls() if url.isLocalFile() and os.path.isdir(url.toLocalFile())), None):
            self.folder_selected.emit(url.toLocalFile())
    def browse_folder(self):
        from PySide6.QtWidgets import QFileDialog
        if folder := QFileDialog.getExistingDirectory(self, "Select Folder"): self.folder_selected.emit(folder)

class PhotoThumbnail(QFrame):
    def __init__(self, file_path, ai_score, parent=None):
        super().__init__(parent)
        self.setFixedSize(180, 200)
        border_color = "#2ECC71" if ai_score >= 80 else "#4A90E2" if ai_score >= 60 else "#E74C3C"
        self.setStyleSheet(f"background-color: #FFFFFF; border-radius: 8px; border: 2px solid {border_color};")
        layout = QVBoxLayout(self)
        pixmap = QPixmap(file_path).scaled(170, 140, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        img_label = QLabel()
        img_label.setPixmap(pixmap)
        layout.addWidget(img_label, 0, Qt.AlignCenter)
        layout.addWidget(QLabel(f"Score: {ai_score}", alignment=Qt.AlignCenter), 0, Qt.AlignCenter)
        layout.addWidget(QLabel(os.path.basename(file_path), alignment=Qt.AlignCenter), 0, Qt.AlignCenter)

class HomePage(QWidget):
    analysis_complete = Signal(list, str)
    def __init__(self, main_window):
        super().__init__()
        self.main_window, self.photos_data, self.source_folder, self.worker = main_window, [], None, None
        layout = QVBoxLayout(self)
        drag_drop = DragDropArea()
        drag_drop.folder_selected.connect(self.load_folder)
        layout.addWidget(drag_drop)
        self.grid_layout = QGridLayout()
        grid_widget = QWidget()
        grid_widget.setLayout(self.grid_layout)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(grid_widget)
        layout.addWidget(scroll)
        self.status_label, self.progress_bar = QLabel("Status: Ready"), QProgressBar()
        self.cancel_button = ModernButton("Cancel Analysis")
        self.cancel_button.clicked.connect(self.cancel_analysis)
        self.cancel_button.setVisible(False)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.cancel_button)

    def load_folder(self, folder):
        self.source_folder = folder
        self.clear_grid()
        self.photos_data.clear()
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.heic', '.webp', '.tiff', '.cr2', '.nef', '.arw']
        image_files = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(tuple(image_extensions))]
        if not image_files: return
        self.cancel_button.setVisible(True)
        self.worker = AnalysisWorker(image_files, self.main_window.log_message)
        self.worker.image_analyzed.connect(self.update_ui)
        self.worker.finished.connect(self.analysis_finished)
        self.worker.start()

    def analysis_finished(self):
        self.cancel_button.setVisible(False)
        if not self.worker.is_cancelled:
            self.analysis_complete.emit(self.photos_data, self.source_folder)

    def cancel_analysis(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.main_window.log_message('info', 'HomePage', "Analysis cancelled by user.")

    def update_ui(self, data):
        self.photos_data.append(data)
        self.progress_bar.setValue(data['progress'])
        thumb = PhotoThumbnail(data['path'], data.get('ai_score', 0))
        self.grid_layout.addWidget(thumb, (len(self.photos_data) - 1) // 4, (len(self.photos_data) - 1) % 4)

    def clear_grid(self):
        while item := self.grid_layout.takeAt(0):
            if widget := item.widget(): widget.deleteLater()
