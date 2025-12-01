
import sys
import os
import shutil
import json
import csv
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFrame, QFileDialog, QListWidget,
                             QListWidgetItem, QRadioButton, QProgressBar, QDialog,
                             QGridLayout)
from PyQt6.QtGui import QPixmap, QTransform, QIcon
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QDateTime
from image_analyzer import ImageAnalyzer
from PIL import Image
import piexif

class Worker(QThread):
    file_processed = pyqtSignal(dict)
    finished = pyqtSignal()

    def __init__(self, file_list, analyzer):
        super().__init__()
        self.file_list = file_list
        self.analyzer = analyzer

    def run(self):
        total_files = len(self.file_list)
        for i, file_path in enumerate(self.file_list):
            if self.isInterruptionRequested():
                break

            basic_info = self.analyzer.get_basic_info(file_path)
            exif_data = self.analyzer.get_exif(file_path)
            img_hash = self.analyzer.get_hash(file_path)
            ai_score, ai_reasons = self.analyzer.get_ai_score(file_path)

            self.file_processed.emit({
                'path': file_path,
                'hash': img_hash,
                'info': basic_info,
                'exif': exif_data,
                'ai_score': ai_score,
                'ai_reasons': ai_reasons,
                'progress': int(((i + 1) / total_files) * 100)
            })
        self.finished.emit()

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About SPAI")
        self.setFixedSize(300, 200)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_label = QLabel()
        logo_pixmap = QPixmap('logo.png').scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio)
        logo_label.setPixmap(logo_pixmap)
        layout.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel("SPAI - Smart Photo AI")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        creator_label = QLabel("Created by: @wawansft")
        layout.addWidget(creator_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)

class PhotoSorterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('SPAI - Photo Sorter')
        self.setGeometry(100, 100, 1600, 900)
        self.setWindowIcon(QIcon('logo.png'))

        self.all_photos = []
        self.undo_stack = []
        self.current_pixmap = None
        self.worker = None
        self.source_folder = None
        self.output_base_dir = None
        self.image_analyzer = ImageAnalyzer() # Create a single analyzer instance

        main_layout = QVBoxLayout(self)
        header = self.create_header()
        content_layout = QHBoxLayout()
        left_panel = self.create_left_panel()
        right_panel = self.create_right_panel()

        content_layout.addWidget(left_panel, 1)
        content_layout.addWidget(right_panel, 4)

        main_layout.addLayout(header)
        main_layout.addLayout(content_layout)

        self.setLayout(main_layout)
        self.set_stylesheet()
        self.manual_mode_radio.setChecked(True)

    def create_header(self):
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 10, 10, 10)

        logo_label = QLabel()
        logo_pixmap = QPixmap('logo.png').scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio)
        logo_label.setPixmap(logo_pixmap)
        header_layout.addWidget(logo_label)

        title_label = QLabel("SPAI")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self.manual_mode_radio = QRadioButton("Manual Mode")
        self.ai_mode_radio = QRadioButton("AI Mode")
        self.manual_mode_radio.toggled.connect(self.toggle_mode)

        mode_group_box = QFrame()
        mode_layout = QHBoxLayout(mode_group_box)
        mode_layout.addWidget(self.manual_mode_radio)
        mode_layout.addWidget(self.ai_mode_radio)
        header_layout.addWidget(mode_group_box)

        about_btn = QPushButton("About")
        about_btn.clicked.connect(self.show_about_dialog)
        header_layout.addWidget(about_btn)

        return header_layout

    def create_left_panel(self):
        panel = QFrame(self)
        panel.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(panel)

        self.folder_btn = QPushButton('Choose Folder')
        self.folder_btn.clicked.connect(self.load_folder)

        self.file_list_widget = QListWidget()
        self.file_list_widget.currentItemChanged.connect(self.list_item_selected)

        # Info Panel
        info_panel = QFrame(self); info_panel.setFrameShape(QFrame.Shape.StyledPanel)
        info_layout = QGridLayout(info_panel)
        self.filename_label = QLabel('File: -')
        self.aiscore_label = QLabel('AI Score: -')
        self.metadata_label = QLabel('EXIF: -')
        self.similar_label = QLabel('Similar: -')
        info_layout.addWidget(self.filename_label, 0, 0)
        info_layout.addWidget(self.aiscore_label, 1, 0)
        info_layout.addWidget(self.metadata_label, 2, 0)
        info_layout.addWidget(self.similar_label, 3, 0)

        self.ai_mode_panel = self.create_ai_mode_panel()

        layout.addWidget(self.folder_btn)
        layout.addWidget(self.file_list_widget)
        layout.addWidget(info_panel)
        layout.addWidget(self.ai_mode_panel)
        layout.addStretch()
        return panel

    def create_right_panel(self):
        panel = QFrame(self)
        panel.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(panel)

        self.photo_preview = QLabel('Select a folder to begin.')
        self.photo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo_preview.setMinimumSize(800, 600)

        rotate_layout = QHBoxLayout()
        self.rotate_left_btn = QPushButton('Rotate Left')
        self.rotate_right_btn = QPushButton('Rotate Right')
        self.rotate_left_btn.clicked.connect(lambda: self.rotate_image(-90))
        self.rotate_right_btn.clicked.connect(lambda: self.rotate_image(90))
        rotate_layout.addWidget(self.rotate_left_btn)
        rotate_layout.addWidget(self.rotate_right_btn)

        layout.addWidget(self.photo_preview)
        layout.addLayout(rotate_layout)
        return panel

    def create_ai_mode_panel(self):
        panel = QFrame(self)
        panel.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(panel)

        title = QLabel("AI Mode Controls")
        title.setStyleSheet("font-weight: bold;")

        self.copy_mode_radio = QRadioButton("Copy Files")
        self.move_mode_radio = QRadioButton("Move Files")
        self.copy_mode_radio.setChecked(True)

        self.start_ai_btn = QPushButton("Start AI Sort")
        self.start_ai_btn.clicked.connect(self.start_ai_mode)

        self.progress_bar = QProgressBar()

        layout.addWidget(title)
        layout.addWidget(self.copy_mode_radio)
        layout.addWidget(self.move_mode_radio)
        layout.addWidget(self.start_ai_btn)
        layout.addWidget(self.progress_bar)
        panel.setVisible(False)
        return panel

    def toggle_mode(self, is_manual):
        self.ai_mode_panel.setVisible(not is_manual)
        self.file_list_widget.setEnabled(is_manual)
        self.rotate_left_btn.setEnabled(is_manual)
        self.rotate_right_btn.setEnabled(is_manual)

    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder: return

        self.source_folder = folder
        self.output_base_dir = os.path.dirname(folder)
        self.all_photos = []
        self.file_list_widget.clear()

        image_files = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
            self.worker.wait()

        self.progress_bar.setValue(0)
        self.worker = Worker(image_files, self.image_analyzer)
        self.worker.file_processed.connect(self.add_photo_data)
        self.worker.finished.connect(self.processing_finished)
        self.worker.start()

    def add_photo_data(self, data):
        self.all_photos.append(data)
        item = QListWidgetItem(os.path.basename(data['path']))
        item.setData(Qt.ItemDataRole.UserRole, data['path'])
        self.file_list_widget.addItem(item)
        self.progress_bar.setValue(data['progress'])

    def processing_finished(self):
        self.find_similar_images()
        if self.file_list_widget.count() > 0:
            self.file_list_widget.setCurrentRow(0)

    def find_similar_images(self, threshold=5):
        for i, photo in enumerate(self.all_photos):
            photo['similar'] = []
            if photo['hash'] is None: continue
            for j, other in enumerate(self.all_photos):
                if i == j or other['hash'] is None: continue
                if photo['hash'] - other['hash'] < threshold:
                    photo['similar'].append(other['path'])

    def list_item_selected(self, current, previous):
        if current is None: return
        path = current.data(Qt.ItemDataRole.UserRole)
        self.display_photo(path)

    def display_photo(self, path):
        photo_data = next((p for p in self.all_photos if p['path'] == path), None)
        if not photo_data: return

        self.current_pixmap = QPixmap(path)
        self.update_pixmap_display()

        self.filename_label.setText(f"File: {os.path.basename(path)}")
        score = photo_data.get('ai_score', 'N/A')
        reasons = ", ".join(photo_data.get('ai_reasons', []))
        self.aiscore_label.setText(f"AI Score: {score} ({reasons})")
        exif = photo_data['exif']
        self.metadata_label.setText(f"EXIF: ISO {exif.get('iso', 'N/A')}, {exif.get('shutter_speed', 'N/A')}, {exif.get('aperture', 'N/A')}")

        similar_count = len(photo_data.get('similar', []))
        self.similar_label.setText(f"Similar: {'Yes' if similar_count > 0 else 'No'}" + (f" ({similar_count})" if similar_count > 0 else ""))

    def update_pixmap_display(self):
        if self.current_pixmap:
            scaled = self.current_pixmap.scaled(self.photo_preview.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.photo_preview.setPixmap(scaled)

    def rotate_image(self, angle):
        current_item = self.file_list_widget.currentItem()
        if not current_item: return
        file_path = current_item.data(Qt.ItemDataRole.UserRole)
        try:
            img = Image.open(file_path)
            exif_dict = piexif.load(img.info.get('exif', b''))
            if angle == -90:
                img = img.transpose(Image.Transpose.ROTATE_270)
            elif angle == 90:
                img = img.transpose(Image.Transpose.ROTATE_90)
            img.save(file_path, "jpeg", exif=piexif.dump(exif_dict), quality=95)
            self.current_pixmap = QPixmap(file_path) # Refresh pixmap
            self.update_pixmap_display()
        except Exception as e:
            print(f"Error rotating image {file_path}: {e}")

    def keyPressEvent(self, event):
        if not self.manual_mode_radio.isChecked(): return
        key = event.key()
        current_row = self.file_list_widget.currentRow()
        if current_row == -1: return

        if key == Qt.Key.Key_Right or key == Qt.Key.Key_Down:
            self.file_list_widget.setCurrentRow(min(current_row + 1, self.file_list_widget.count() - 1))
        elif key == Qt.Key.Key_Left or key == Qt.Key.Key_Up:
            self.file_list_widget.setCurrentRow(max(current_row - 1, 0))
        elif key in (Qt.Key.Key_1, Qt.Key.Key_2, Qt.Key.Key_3, Qt.Key.Key_X, Qt.Key.Key_S):
            if key == Qt.Key.Key_S:
                 self.file_list_widget.setCurrentRow(min(current_row + 1, self.file_list_widget.count() - 1))
                 return

            dest_map = {Qt.Key.Key_1: 'sortir_1', Qt.Key.Key_2: 'sortir_2', Qt.Key.Key_3: 'sortir_3', Qt.Key.Key_X: 'rejected'}
            self.move_current_photo(dest_map[key])
        elif key == Qt.Key.Key_Z:
            self.undo_last_move()

    def move_current_photo(self, dest_subfolder):
        current_item = self.file_list_widget.currentItem()
        if not current_item: return

        source_path = current_item.data(Qt.ItemDataRole.UserRole)
        filename = os.path.basename(source_path)
        dest_folder = os.path.join(self.output_base_dir, dest_subfolder)
        os.makedirs(dest_folder, exist_ok=True)
        dest_path = os.path.join(dest_folder, filename)

        try:
            shutil.move(source_path, dest_path)
            row = self.file_list_widget.row(current_item)
            photo_data = next((p for p in self.all_photos if p['path'] == source_path), None)
            if photo_data: self.all_photos.remove(photo_data)
            self.file_list_widget.takeItem(row)
            self.undo_stack.append({'from': dest_path, 'to': source_path, 'data': photo_data, 'row': row})
            print(f"Moved {filename} to {dest_folder}")
        except Exception as e:
            print(f"Could not move {filename}: {e}")

    def undo_last_move(self):
        if not self.undo_stack: return
        last_move = self.undo_stack.pop()
        try:
            shutil.move(last_move['from'], last_move['to'])
            self.all_photos.insert(last_move['row'], last_move['data'])
            item = QListWidgetItem(os.path.basename(last_move['to']))
            item.setData(Qt.ItemDataRole.UserRole, last_move['to'])
            self.file_list_widget.insertItem(last_move['row'], item)
            self.file_list_widget.setCurrentRow(last_move['row'])
            print(f"Undid move of {os.path.basename(last_move['to'])}")
        except Exception as e:
            print(f"Could not undo move: {e}")

    def start_ai_mode(self):
        if not self.all_photos:
            print("No photos to process.")
            return

        is_move_mode = self.move_mode_radio.isChecked()
        operation = shutil.move if is_move_mode else shutil.copy

        folders = {
            'Best': os.path.join(self.output_base_dir, 'Best'),
            'Good': os.path.join(self.output_base_dir, 'Good'),
            'Reject': os.path.join(self.output_base_dir, 'Reject')
        }
        for folder in folders.values():
            os.makedirs(folder, exist_ok=True)

        rated_folder = os.path.join(self.output_base_dir, 'rated')
        os.makedirs(rated_folder, exist_ok=True)

        all_ratings = []

        total_files = len(self.all_photos)
        for i, photo_data in enumerate(self.all_photos):
            score = photo_data.get('ai_score', 0)
            source_path = photo_data['path']
            filename = os.path.basename(source_path)

            if 80 <= score <= 100:
                dest_folder = folders['Best']
            elif 60 <= score <= 79:
                dest_folder = folders['Good']
            else:
                dest_folder = folders['Reject']

            dest_path = os.path.join(dest_folder, filename)

            try:
                operation(source_path, dest_path)
            except Exception as e:
                print(f"Could not {operation.__name__} {filename}: {e}")

            all_ratings.append({
                'filename': filename,
                'score': score,
                'reasons': photo_data.get('ai_reasons', []),
                'path': dest_path
            })
            self.progress_bar.setValue(int(((i + 1) / total_files) * 100))

        # Save results
        with open(os.path.join(rated_folder, 'ratings.json'), 'w') as f:
            json.dump(all_ratings, f, indent=4)

        with open(os.path.join(rated_folder, 'ratings.csv'), 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['filename', 'score', 'reasons', 'path'])
            for item in all_ratings:
                writer.writerow([item['filename'], item['score'], ", ".join(item['reasons']), item['path']])

        print("AI sorting complete. Results saved in 'rated' folder.")
        # Optionally, clear the list if files were moved
        if is_move_mode:
            self.all_photos.clear()
            self.file_list_widget.clear()


    def show_about_dialog(self):
        dialog = AboutDialog(self)
        dialog.exec()

    def set_stylesheet(self):
        self.setStyleSheet("""
            QWidget { background-color: #2b2b2b; color: #f0f0f0; font-family: 'Segoe UI'; }
            QFrame { border: 1px solid #444; border-radius: 4px; }
            QPushButton { background-color: #007acc; color: white; border: none; padding: 10px; border-radius: 4px; }
            QPushButton:hover { background-color: #005a9e; }
            QPushButton:pressed { background-color: #003e6e; }
            QListWidget { border: 1px solid #444; background-color: #3c3c3c; }
            QListWidget::item { padding: 8px; }
            QListWidget::item:selected { background-color: #007acc; color: white; }
            QLabel { padding: 4px; font-size: 14px; }
            QRadioButton { font-size: 14px; }
            QProgressBar { text-align: center; }
        """)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = PhotoSorterApp()
    ex.show()
    sys.exit(app.exec())
