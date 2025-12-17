
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QRadioButton, QHBoxLayout, QProgressBar
from ui.widgets import ModernCard, ModernButton
from backend.workers import FileWorker
import os

class AIModePage(QWidget):
    def __init__(self, main_window, settings_page):
        super().__init__()
        self.main_window, self.settings_page, self.photos_data, self.source_folder, self.file_worker = main_window, settings_page, [], None, None
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("🤖 AI Mode Results", styleSheet="font-size: 28px; font-weight: 700;"))
        summary_card = ModernCard()
        summary_layout = QGridLayout(summary_card)
        self.best_label, self.good_label, self.reject_label = QLabel("Best (80-100): 0"), QLabel("Good (60-79): 0"), QLabel("Reject (0-59): 0")
        summary_layout.addWidget(self.best_label, 0, 0)
        summary_layout.addWidget(self.good_label, 1, 0)
        summary_layout.addWidget(self.reject_label, 2, 0)
        layout.addWidget(summary_card)
        self.copy_radio, self.move_radio = QRadioButton("Copy Mode"), QRadioButton("Move Mode")
        self.move_radio.setChecked(True)
        radio_layout = QHBoxLayout()
        radio_layout.addWidget(self.copy_radio)
        radio_layout.addWidget(self.move_radio)
        layout.addLayout(radio_layout)
        self.start_sort_button = ModernButton("Start Sorting")
        self.start_sort_button.clicked.connect(self.start_sorting)
        layout.addWidget(self.start_sort_button)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        layout.addStretch()
        self.start_sort_button.setEnabled(False)
        self.copy_radio.setEnabled(False)
        self.move_radio.setEnabled(False)

    def set_photo_data(self, photos, folder):
        self.photos_data, self.source_folder = photos, folder
        self.display_summary()
        self.start_sort_button.setEnabled(True)
        self.copy_radio.setEnabled(True)
        self.move_radio.setEnabled(True)

    def display_summary(self):
        best = sum(1 for p in self.photos_data if p.get('ai_score', 0) >= 80)
        good = sum(1 for p in self.photos_data if 60 <= p.get('ai_score', 0) < 80)
        self.best_label.setText(f"Best (80-100): {best} photos")
        self.good_label.setText(f"Good (60-79): {good} photos")
        self.reject_label.setText(f"Reject (0-59): {len(self.photos_data) - best - good} photos")

    def start_sorting(self):
        op = 'copy' if self.copy_radio.isChecked() else 'move'
        if not self.photos_data: return
        files = []
        output_dir = self.settings_page.output_folder
        for p in self.photos_data:
            score = p.get('ai_score', 0)
            folder = "Best" if score >= 80 else "Good" if score >= 60 else "Reject"
            files.append((p['path'], os.path.join(output_dir, "rated", folder, os.path.basename(p['path']))))
        self.progress_bar.setVisible(True)
        self.start_sort_button.setEnabled(False)
        self.file_worker = FileWorker(files, op, self.main_window.log_message)
        self.file_worker.progress.connect(self.progress_bar.setValue)
        self.file_worker.finished.connect(self.sorting_finished)
        self.file_worker.start()

    def sorting_finished(self):
        self.progress_bar.setVisible(False)
        self.start_sort_button.setEnabled(True)
