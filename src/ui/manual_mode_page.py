
import os
import shutil
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QGridLayout, QRadioButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QTransform
from PIL import Image
import piexif
from ui.widgets import ModernButton, ModernCard

class ManualModePage(QWidget):
    def __init__(self, main_window, settings_page):
        super().__init__()
        self.main_window, self.settings_page, self.photos, self.source_folder, self.current_index, self.undo_stack = main_window, settings_page, [], None, -1, []
        self.pixmap_rotations = {}
        main_layout = QHBoxLayout(self)
        self.photo_preview = QLabel("Select a folder on the Home page.")
        self.photo_preview.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.photo_preview, 1)
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        info_card = ModernCard()
        info_layout = QVBoxLayout(info_card)
        self.filename_label, self.ai_score_label, self.similar_label = QLabel("Filename: -"), QLabel("AI Score: -"), QLabel("Similar: -")
        info_layout.addWidget(self.filename_label)
        info_layout.addWidget(self.ai_score_label)
        info_layout.addWidget(self.similar_label)
        right_layout.addWidget(info_card)
        controls_card = ModernCard()
        controls_layout = QGridLayout(controls_card)
        self.rotate_left_btn, self.rotate_right_btn, self.undo_btn = ModernButton("Rotate Left"), ModernButton("Rotate Right"), ModernButton("Undo")
        self.rotate_left_btn.clicked.connect(lambda: self.rotate_image(-90))
        self.rotate_right_btn.clicked.connect(lambda: self.rotate_image(90))
        self.undo_btn.clicked.connect(self.undo_last_move)
        controls_layout.addWidget(self.rotate_left_btn, 0, 0)
        controls_layout.addWidget(self.rotate_right_btn, 0, 1)
        controls_layout.addWidget(self.undo_btn, 1, 0, 1, 2)
        self.copy_radio, self.move_radio = QRadioButton("Copy Mode"), QRadioButton("Move Mode")
        self.move_radio.setChecked(True)
        controls_layout.addWidget(self.copy_radio, 2, 0)
        controls_layout.addWidget(self.move_radio, 2, 1)
        right_layout.addWidget(controls_card)
        main_layout.addWidget(right_panel)

    def set_photo_data(self, photos, folder):
        self.photos, self.source_folder = photos, folder
        if self.photos: self.current_index = 0; self.display_current_photo()

    def display_current_photo(self):
        if 0 <= self.current_index < len(self.photos):
            photo = self.photos[self.current_index]
            path = photo['path']
            pixmap = QPixmap(path)

            # Apply in-memory rotation if it exists
            rotation = self.pixmap_rotations.get(path, 0)
            if rotation != 0:
                transform = QTransform().rotate(rotation)
                pixmap = pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)

            scaled_pixmap = pixmap.scaled(self.photo_preview.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.photo_preview.setPixmap(scaled_pixmap)

            self.filename_label.setText(f"File: {os.path.basename(path)}")
            self.ai_score_label.setText(f"AI Score: {photo.get('ai_score', 'N/A')}")
            self.similar_label.setText(f"Similar: Yes ({len(photo.get('similar', []))})" if photo.get('similar') else "Similar: No")

    def navigate_photo(self, delta):
        if self.photos:
            self.current_index = max(0, min(self.current_index + delta, len(self.photos) - 1))
            self.display_current_photo()

    def handle_sort_key(self, key):
        dest_map = {Qt.Key.Key_1: 'sortir_1', Qt.Key.Key_2: 'sortir_2', Qt.Key.Key_3: 'sortir_3', Qt.Key.Key_X: 'rejected'}
        op = 'copy' if self.copy_radio.isChecked() else 'move'
        if not (0 <= self.current_index < len(self.photos)):
            return
        photo = self.photos[self.current_index]
        source_path = photo['path']
        output_dir = self.settings_page.output_folder
        dest_path = os.path.join(output_dir, "manual_sort", dest_map[key], os.path.basename(source_path))

        try:
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            (shutil.copy if op == 'copy' else shutil.move)(source_path, dest_path)
            self.undo_stack.append({'op': op, 'from': dest_path, 'to': source_path, 'data': photo, 'index': self.current_index})

            if op == 'move':
                self.photos.pop(self.current_index)
                self.current_index = min(self.current_index, len(self.photos) - 1)
            else:
                self.navigate_photo(1)

            if self.photos:
                self.display_current_photo()
            else:
                self.photo_preview.setText("All photos sorted!")

        except Exception as e:
            self.main_window.log_message('error', 'ManualMode', f"Failed to {op} {source_path}: {e}")

    def undo_last_move(self):
        if not self.undo_stack: return
        last = self.undo_stack.pop()
        try:
            if last['op'] == 'move': shutil.move(last['from'], last['to']); self.photos.insert(last['index'], last['data'])
            elif last['op'] == 'copy': os.remove(last['from'])
            self.current_index = last['index']
            self.display_current_photo()
        except Exception as e:
            self.main_window.log_message('error', 'ManualMode', f"Failed to undo {last['op']}: {e}")

    def rotate_image(self, angle):
        if not (0 <= self.current_index < len(self.photos)): return
        path = self.photos[self.current_index]['path']

        try:
            exif_dict = piexif.load(path)
            orientation = exif_dict.get("0th", {}).get(piexif.ImageIFD.Orientation, 1)

            # Mapping of EXIF orientation values to rotation angles
            orientation_map = {1: 0, 6: 90, 3: 180, 8: 270}
            current_angle = orientation_map.get(orientation, 0)
            new_angle = (current_angle + angle) % 360

            new_orientation = next((k for k, v in orientation_map.items() if v == new_angle), 1)

            exif_dict["0th"][piexif.ImageIFD.Orientation] = new_orientation
            piexif.insert(piexif.dump(exif_dict), path)

            self.main_window.log_message('info', 'ManualMode', f"Rotated {os.path.basename(path)} by setting EXIF orientation.")
            self.display_current_photo()

        except (piexif.InvalidImageDataError, KeyError, AttributeError):
            # Fallback for non-EXIF images
            if path not in self.pixmap_rotations:
                self.pixmap_rotations[path] = 0
            self.pixmap_rotations[path] = (self.pixmap_rotations[path] + angle) % 360
            self.display_current_photo()
            self.main_window.log_message('info', 'ManualMode', f"Applied in-memory rotation to {os.path.basename(path)}.")
        except Exception as e:
            self.main_window.log_message('error', 'ManualMode', f"Failed to rotate {path}: {e}")
