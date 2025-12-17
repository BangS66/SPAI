
import sys
import os
import datetime
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QStackedWidget
from PySide6.QtCore import Qt
import imagehash

# Import backend and UI components
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from backend.workers import AnalysisWorker, FileWorker
from ui.widgets import SidebarButton, ConfirmDialog
from ui.home_page import HomePage
from ui.ai_mode_page import AIModePage
from ui.manual_mode_page import ManualModePage
from ui.auto_sort_page import AutoSortPage
from ui.other_pages import AboutPage, SettingsPage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SPAI - Smart Photo AI")
        self.setMinimumSize(1200, 800)
        self.photos_data, self.source_folder = [], None

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0,0,0,0)

        sidebar = QFrame(styleSheet="background-color: #2D3E50;")
        sidebar_layout = QVBoxLayout(sidebar)
        self.nav_buttons = {}
        for i, (icon, name) in enumerate([("🏠", "Home"), ("🤖", "AI Mode"), ("✋", "Manual Mode"), ("📋", "Auto Sort"), ("⚙️", "Settings"), ("ℹ️", "About")]):
            btn = SidebarButton(name, icon)
            btn.clicked.connect(lambda _, i=i, b=btn: self.change_page(i, b))
            sidebar_layout.addWidget(btn)
            self.nav_buttons[name] = btn
        self.nav_buttons["Home"].setChecked(True) # Set initial page
        sidebar_layout.addStretch()

        self.stacked_widget = QStackedWidget()
        self.settings_page = SettingsPage()
        self.home_page = HomePage(self)
        self.ai_page = AIModePage(self, self.settings_page)
        self.manual_page = ManualModePage(self, self.settings_page)
        self.auto_sort_page = AutoSortPage(self, self.settings_page)
        self.about_page = AboutPage()

        self.stacked_widget.addWidget(self.home_page)
        self.stacked_widget.addWidget(self.ai_page)
        self.stacked_widget.addWidget(self.manual_page)
        self.stacked_widget.addWidget(self.auto_sort_page)
        self.stacked_widget.addWidget(self.settings_page)
        self.stacked_widget.addWidget(self.about_page)

        content_layout = QHBoxLayout()
        content_layout.addWidget(sidebar)
        content_layout.addWidget(self.stacked_widget, 1)
        main_layout.addLayout(content_layout)

        self.setCentralWidget(main_widget)
        self.home_page.analysis_complete.connect(self.handle_analysis_complete)

    def change_page(self, index, button):
        self.stacked_widget.setCurrentIndex(index)
        for btn in self.nav_buttons.values():
            btn.setChecked(False)
        button.setChecked(True)

    def handle_analysis_complete(self, photos, folder):
        self.photos_data, self.source_folder = photos, folder
        self.find_similar_images()
        self.ai_page.set_photo_data(photos, folder)
        self.manual_page.set_photo_data(photos, folder)
        self.auto_sort_page.set_photo_data(photos, folder)

    def find_similar_images(self, threshold=5):
        for i, photo in enumerate(self.photos_data):
            photo['similar'] = []
            if not photo.get('hash'): continue
            h1 = imagehash.hex_to_hash(photo['hash'])
            for j, other in enumerate(self.photos_data):
                if i != j and other.get('hash'):
                    if h1 - imagehash.hex_to_hash(other['hash']) < threshold:
                        photo['similar'].append(other['path'])

    def log_message(self, level, context, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("spai.log", "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] [{level.upper()}] [{context}] {message}\n")

    def keyPressEvent(self, event):
        if self.stacked_widget.currentWidget() == self.manual_page:
            key = event.key()
            if key in [Qt.Key.Key_Left, Qt.Key.Key_Up]: self.manual_page.navigate_photo(-1)
            elif key in [Qt.Key.Key_Right, Qt.Key.Key_Down, Qt.Key.Key_S]: self.manual_page.navigate_photo(1)
            elif key in [Qt.Key.Key_1, Qt.Key.Key_2, Qt.Key.Key_3, Qt.Key.Key_X]: self.manual_page.handle_sort_key(key)
            elif key == Qt.Key.Key_Z: self.manual_page.undo_last_move()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
