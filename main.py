
import sys
import os
import shutil
import csv
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFrame, QFileDialog, QListWidget,
                             QListWidgetItem, QRadioButton, QProgressBar)
from PyQt6.QtGui import QPixmap, QTransform
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QDateTime
from image_analyzer import ImageAnalyzer
from PIL import Image
import piexif

class Worker(QThread):
    file_processed = pyqtSignal(dict)
    finished = pyqtSignal()

    def __init__(self, file_list):
        super().__init__()
        self.file_list = file_list
        self.analyzer = ImageAnalyzer()

    def run(self):
        for file_path in self.file_list:
            if self.isInterruptionRequested():
                break

            basic_info = self.analyzer.get_basic_info(file_path)
            exif_data = self.analyzer.get_exif(file_path)
            img_hash = self.analyzer.get_hash(file_path)

            self.file_processed.emit({
                'path': file_path,
                'hash': img_hash,
                'info': basic_info,
                'exif': exif_data
            })
        self.finished.emit()

class PhotoSorterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Photo Sorter - Manual Mode')
        self.setGeometry(100, 100, 1400, 900)

        self.all_photos = []
        self.undo_stack = []
        self.current_pixmap = None
        self.worker = None

        main_layout = QHBoxLayout(self)
        left_panel = self.create_left_panel()
        right_panel = self.create_right_panel()

        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 4)

        self.setLayout(main_layout)
        self.set_stylesheet()

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
        info_layout = QVBoxLayout(info_panel)
        self.filename_label = QLabel('Filename: -')
        self.info_label = QLabel('Size/Dims: -')
        self.metadata_label = QLabel('Metadata: -')
        self.similar_label = QLabel('Similar: -')
        info_layout.addWidget(self.filename_label); info_layout.addWidget(self.info_label)
        info_layout.addWidget(self.metadata_label); info_layout.addWidget(self.similar_label)

        layout.addWidget(self.folder_btn)
        layout.addWidget(self.file_list_widget)
        layout.addWidget(info_panel)
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

    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder: return

        self.all_photos = []
        self.file_list_widget.clear()

        image_files = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
            self.worker.wait()

        self.worker = Worker(image_files)
        self.worker.file_processed.connect(self.add_photo_data)
        self.worker.finished.connect(self.processing_finished)
        self.worker.start()

    def add_photo_data(self, data):
        self.all_photos.append(data)
        item = QListWidgetItem(os.path.basename(data['path']))
        item.setData(Qt.ItemDataRole.UserRole, data['path'])
        self.file_list_widget.addItem(item)

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
        self.info_label.setText(f"Size: {photo_data['info'].get('size_mb', 'N/A')}, Dims: {photo_data['info'].get('dimensions', 'N/A')}")
        exif = photo_data['exif']
        self.metadata_label.setText(f"ISO: {exif.get('iso', 'N/A')}, Shutter: {exif.get('shutter_speed', 'N/A')}, Aperture: {exif.get('aperture', 'N/A')}")

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
            # Load image and exif data
            img = Image.open(file_path)
            exif_dict = piexif.load(img.info.get('exif', b''))

            # Rotate the image
            if angle == -90:
                img = img.transpose(Image.ROTATE_270)
            elif angle == 90:
                img = img.transpose(Image.ROTATE_90)

            # Save the rotated image with original EXIF data
            img.save(file_path, "jpeg", exif=piexif.dump(exif_dict), quality=95)

            # Refresh the preview
            self.current_pixmap = QPixmap(file_path)
            self.update_pixmap_display()
            self.log_action(f"ROTATED: {file_path} by {angle} degrees")

        except Exception as e:
            print(f"Error rotating image {file_path}: {e}")
            self.log_action(f"ERROR: Failed to rotate {file_path}: {e}")

    def keyPressEvent(self, event):
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

    def move_current_photo(self, dest_folder):
        current_item = self.file_list_widget.currentItem()
        if not current_item: return

        source_path = current_item.data(Qt.ItemDataRole.UserRole)
        filename = os.path.basename(source_path)

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

    def log_action(self, message):
        """Logs an action to a file."""
        log_file = "photo_sorter.log"
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        with open(log_file, 'a') as f:
            f.write(f"[{timestamp}] {message}\n")

    def set_stylesheet(self):
        self.setStyleSheet("""
            QWidget { background-color: #2b2b2b; color: #f0f0f0; font-size: 14px; }
            QPushButton { background-color: #555; border: 1px solid #777; padding: 8px; border-radius: 4px; }
            QPushButton:hover { background-color: #666; }
            QPushButton:pressed { background-color: #444; }
            QFrame { border: 1px solid #444; border-radius: 4px; }
            QLabel { padding: 4px; }
            QListWidget { border: 1px solid #444; background-color: #3c3c3c; }
            QListWidget::item { padding: 5px; }
            QListWidget::item:selected { background-color: #007acc; color: white; }
        """)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = PhotoSorterApp()
    ex.show()
    sys.exit(app.exec())
