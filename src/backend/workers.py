
import os
import shutil
from PySide6.QtCore import QThread, Signal
from backend.image_analyzer import ImageAnalyzer

class FileWorker(QThread):
    progress = Signal(int)
    finished = Signal()
    def __init__(self, files_to_process, operation, logger):
        super().__init__()
        self.files, self.operation, self.logger = files_to_process, operation, logger
    def run(self):
        op_func = shutil.copy if self.operation == 'copy' else shutil.move
        for i, (src, dest) in enumerate(self.files):
            try:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                op_func(src, dest)
            except Exception as e:
                self.logger('error', 'FileWorker', f"Failed to {self.operation} {src}: {e}")
            self.progress.emit(int(((i + 1) / len(self.files)) * 100))
        self.finished.emit()

class AnalysisWorker(QThread):
    image_analyzed = Signal(dict)
    finished = Signal()
    def __init__(self, image_paths, logger):
        super().__init__()
        self.image_paths, self.logger = image_paths, logger
        self.analyzer = ImageAnalyzer(logger)
        self.is_cancelled = False
    def run(self):
        for i, path in enumerate(self.image_paths):
            if self.is_cancelled:
                break
            result = {'path': path, 'progress': int(((i + 1) / len(self.image_paths)) * 100)}
            result.update(self.analyzer.analyze_image_quality(path))
            self.image_analyzed.emit(result)
        self.finished.emit()
    def stop(self):
        self.is_cancelled = True
