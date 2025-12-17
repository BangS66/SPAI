
import os
import re
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea, QProgressBar
from ui.widgets import ModernButton, ConfirmDialog
from backend.workers import FileWorker

class AutoSortPage(QWidget):
    def __init__(self, main_window, settings_page):
        super().__init__()
        self.main_window, self.settings_page, self.photos, self.source_folder, self.grouped_files, self.file_worker = main_window, settings_page, [], None, {}, None
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("📋 Auto Sort by Filename", styleSheet="font-size: 28px; font-weight: 700;"))
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.groups_widget = QWidget()
        self.groups_layout = QVBoxLayout(self.groups_widget)
        self.scroll_area.setWidget(self.groups_widget)
        layout.addWidget(self.scroll_area)
        self.sort_button = ModernButton("Sort Files")
        self.sort_button.clicked.connect(self.show_confirmation)
        layout.addWidget(self.sort_button)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

    def set_photo_data(self, photos, folder):
        self.photos, self.source_folder = photos, folder
        self.analyze_filenames()

    def analyze_filenames(self):
        self.grouped_files.clear()
        for photo in self.photos:
            # Improved regex to handle date-like prefixes and more characters
            match = re.match(r'^([a-zA-Z0-9_-]+[a-zA-Z_-])', os.path.basename(photo['path']))
            if match:
                prefix = match.group(1).strip()
                if prefix not in self.grouped_files: self.grouped_files[prefix] = []
                self.grouped_files[prefix].append(photo['path'])
        self.display_groups()

    def display_groups(self):
        while item := self.groups_layout.takeAt(0):
            if widget := item.widget(): widget.deleteLater()
        for prefix, files in self.grouped_files.items():
            box = QFrame()
            layout = QVBoxLayout(box)
            layout.addWidget(QLabel(f"Group: {prefix} ({len(files)} files)"))
            for file in files[:3]: layout.addWidget(QLabel(os.path.basename(file)))
            self.groups_layout.addWidget(box)

    def show_confirmation(self):
        dialog = ConfirmDialog(self)
        if dialog.exec() and dialog.operation: self.start_sorting(dialog.operation)

    def start_sorting(self, op):
        files = []
        output_dir = self.settings_page.output_folder
        for prefix, paths in self.grouped_files.items():
            for path in paths:
                files.append((path, os.path.join(output_dir, "auto_sorted", prefix, os.path.basename(path))))
        self.progress_bar.setVisible(True)
        self.file_worker = FileWorker(files, op, self.main_window.log_message)
        self.file_worker.progress.connect(self.progress_bar.setValue)
        self.file_worker.finished.connect(lambda: self.progress_bar.setVisible(False))
        self.file_worker.start()
