
import imagehash
from PIL import Image
import os
import cv2
import numpy as np
import mediapipe as mp

class ImageAnalyzer:
    def __init__(self):
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(static_image_mode=True, max_num_faces=5)

    def get_basic_info(self, image_path):
        """Gets basic file info like size and dimensions."""
        try:
            stat = os.stat(image_path)
            size_mb = stat.st_size / (1024 * 1024)
            with Image.open(image_path) as img:
                width, height = img.size
            return {"size_mb": f"{size_mb:.2f} MB", "dimensions": f"{width}x{height}"}
        except Exception as e:
            return {}

    def get_exif(self, image_path):
        """Extracts basic EXIF data."""
        try:
            with Image.open(image_path) as img:
                exif_data = img._getexif()
                if not exif_data: return {}
                FNUMBER, EXPOSURE_TIME, ISO_SPEED_RATINGS = 33437, 33434, 34855
                f_number = exif_data.get(FNUMBER)
                exposure_time = exif_data.get(EXPOSURE_TIME)
                iso = exif_data.get(ISO_SPEED_RATINGS)
                shutter_speed = f"1/{int(1/exposure_time)}" if exposure_time and exposure_time < 1 else f"{int(exposure_time)}s" if exposure_time else "N/A"
                return {'aperture': f"f/{f_number}" if f_number else "N/A", 'shutter_speed': shutter_speed, 'iso': iso if iso else "N/A"}
        except Exception as e:
            return {}

    def get_hash(self, image_path):
        """Computes the average hash of an image."""
        try:
            with Image.open(image_path) as img:
                return imagehash.average_hash(img)
        except Exception as e:
            return None

    def analyze_sharpness(self, image):
        """Analyzes the sharpness of an image using Laplacian variance."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        score = min(100, variance / 10) # Normalize score
        reason = "Blurry" if variance < 100 else "Sharp"
        return score, reason

    def analyze_exposure(self, image):
        """Analyzes the exposure of an image using its histogram."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        mean_brightness = np.mean(hist)

        if mean_brightness < 50:
            score = 20
            reason = "Underexposed"
        elif mean_brightness > 200:
            score = 30
            reason = "Overexposed"
        else:
            score = 90
            reason = "Good Exposure"
        return score, reason

    def analyze_faces(self, image):
        """Analyzes faces in the image for open eyes and expressions."""
        results = self.face_mesh.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        if not results.multi_face_landmarks:
            return 100, "No faces detected"

        face_scores = []
        for face_landmarks in results.multi_face_landmarks:
            # Simple eye openness check (can be improved)
            left_eye_pts = face_landmarks.landmark[145]
            right_eye_pts = face_landmarks.landmark[374]
            # A more robust check would involve more landmarks
            is_open = (left_eye_pts.y - face_landmarks.landmark[159].y) > 0.01
            face_scores.append(90 if is_open else 20)

        avg_score = np.mean(face_scores)
        reason = "Eyes Open" if avg_score > 50 else "Eyes Closed"
        return avg_score, reason

    def analyze_composition(self, image):
        """Analyzes the composition for a tilted horizon."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=100, maxLineGap=10)

        if lines is None:
            return 100, "Good Composition"

        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angles.append(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)

        avg_angle = np.mean(angles)
        if abs(avg_angle) > 5:
            return 40, "Tilted Horizon"

        return 95, "Good Composition"

    def get_ai_score(self, image_path):
        """Calculates an overall AI score for the image."""
        try:
            image = cv2.imread(image_path)
            if image is None: return 0, ["Could not read image"]

            scores = {}
            reasons = []

            sharpness_score, sharpness_reason = self.analyze_sharpness(image)
            scores['sharpness'] = sharpness_score
            reasons.append(sharpness_reason)

            exposure_score, exposure_reason = self.analyze_exposure(image)
            scores['exposure'] = exposure_score
            reasons.append(exposure_reason)

            face_score, face_reason = self.analyze_faces(image)
            scores['faces'] = face_score
            reasons.append(face_reason)

            composition_score, comp_reason = self.analyze_composition(image)
            scores['composition'] = composition_score
            reasons.append(comp_reason)

            # Weighted average
            weights = {'sharpness': 0.4, 'exposure': 0.2, 'faces': 0.3, 'composition': 0.1}
            final_score = sum(scores[k] * weights[k] for k in scores)

            return int(final_score), list(set(reasons))

        except Exception as e:
            print(f"Error getting AI score for {image_path}: {e}")
            return 0, ["Analysis Error"]

    def __del__(self):
        self.face_mesh.close()
