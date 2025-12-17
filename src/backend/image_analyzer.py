
import os
import cv2
import numpy as np
import mediapipe as mp
from scipy.spatial import distance as dist
import rawpy
from PIL import Image
import imagehash

class ImageAnalyzer:
    def __init__(self, logger):
        self.logger = logger

    def get_basic_info(self, image_path):
        try:
            stat = os.stat(image_path)
            size_mb = stat.st_size / (1024 * 1024)
            with Image.open(image_path) as img:
                width, height = img.size
            return {"size_mb": f"{size_mb:.2f} MB", "dimensions": f"{width}x{height}"}
        except Exception as e:
            self.logger('error', 'ImageAnalyzer', f"Error getting basic info for {image_path}: {e}")
            return {}

    def get_exif(self, image_path):
        try:
            with Image.open(image_path) as img:
                exif_data = img._getexif()
                if not exif_data: return {}
                FNUMBER, EXPOSURE_TIME, ISO_SPEED_RATINGS = 33437, 33434, 34855
                f_number, exposure_time, iso = exif_data.get(FNUMBER), exif_data.get(EXPOSURE_TIME), exif_data.get(ISO_SPEED_RATINGS)
                shutter_speed = f"1/{int(1/exposure_time)}" if exposure_time and exposure_time < 1 else f"{int(exposure_time)}s" if exposure_time else "N/A"
                return {'aperture': f"f/{f_number}" if f_number else "N/A", 'shutter_speed': shutter_speed, 'iso': iso or "N/A"}
        except Exception as e:
            self.logger('error', 'ImageAnalyzer', f"Error reading EXIF for {image_path}: {e}")
            return {}

    def get_hash(self, image_path):
        try:
            with Image.open(image_path) as img:
                return imagehash.average_hash(img)
        except Exception as e:
            self.logger('error', 'ImageAnalyzer', f"Error hashing {image_path}: {e}")
            return None

    def analyze_image_quality(self, image_path):
        try:
            raw_extensions = ['.cr2', '.nef', '.arw']
            file_ext = os.path.splitext(image_path)[1].lower()
            image = None

            if file_ext in raw_extensions:
                try:
                    with rawpy.imread(image_path) as raw:
                        rgb = raw.postprocess(use_camera_wb=True, half_size=True, no_auto_bright=True, output_bps=8)
                        image = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
                except Exception as e:
                    self.logger('error', 'ImageAnalyzer', f"Failed to decode RAW file {image_path}: {e}")
                    try:
                        # Fallback to thumbnail
                        with rawpy.imread(image_path) as raw:
                            thumb = raw.extract_thumb()
                        image = cv2.imdecode(np.frombuffer(thumb.data, np.uint8), cv2.IMREAD_COLOR)
                    except Exception as thumb_e:
                        self.logger('error', 'ImageAnalyzer', f"Failed to extract thumbnail for {image_path}: {thumb_e}")
                        return {"error": f"RAW decode and thumbnail extraction failed: {thumb_e}"}
            else:
                image = cv2.imread(image_path)

            if image is None:
                self.logger('error', 'ImageAnalyzer', f"Could not read image: {image_path}")
                return {"error": "Could not read image"}

            scores = {
                'sharpness': min(100, self.analyze_sharpness(image) / 1.5),
                'exposure': 100 - abs(self.analyze_exposure(image) - 128),
                'noise': max(0, 100 - self.estimate_noise(image)),
                'hash': str(self.get_hash(image_path)) if self.get_hash(image_path) else None
            }
            scores.update(self.analyze_faces_and_composition(image))

            if scores['face_detected']:
                total_score = (scores['sharpness'] * 0.25 + scores['exposure'] * 0.15 + scores['noise'] * 0.10 +
                               scores['composition_score'] * 0.20 + scores['eyes_open_score'] * 0.20 + scores['smile_score'] * 0.10)
            else:
                total_score = (scores['sharpness'] * 0.4 + scores['exposure'] * 0.3 + scores['noise'] * 0.3)

            scores['ai_score'] = int(min(100, total_score))
            return scores

        except Exception as e:
            self.logger('error', 'ImageAnalyzer', f"Error during AI analysis for {image_path}: {e}")
            return {"error": str(e)}

    def analyze_sharpness(self, image): return cv2.Laplacian(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()
    def analyze_exposure(self, image): return np.mean(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY))
    def estimate_noise(self, image): return np.std(image)

    def _eye_aspect_ratio(self, eye):
        return (dist.euclidean(eye[1], eye[5]) + dist.euclidean(eye[2], eye[4])) / (2.0 * dist.euclidean(eye[0], eye[3]))

    def _mouth_aspect_ratio(self, mouth):
        return (dist.euclidean(mouth[2], mouth[10]) + dist.euclidean(mouth[4], mouth[8])) / (2.0 * dist.euclidean(mouth[0], mouth[6]))

    def analyze_faces_and_composition(self, image):
        scores = {'face_detected': False, 'eyes_open_score': 0, 'smile_score': 0, 'composition_score': 50}
        mp_face_mesh = mp.solutions.face_mesh
        with mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=5, min_detection_confidence=0.5) as face_mesh:
            results = face_mesh.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            if not results.multi_face_landmarks: return scores

            scores['face_detected'] = True
            h, w, _ = image.shape
            main_face = max(results.multi_face_landmarks, key=lambda lms: (max(lm.x for lm in lms.landmark) - min(lm.x for lm in lms.landmark)) *
                                                                         (max(lm.y for lm in lms.landmark) - min(lm.y for lm in lms.landmark)))
            landmarks = np.array([(lm.x, lm.y) for lm in main_face.landmark])

            left_ear = self._eye_aspect_ratio(landmarks[[362, 385, 387, 263, 373, 380]])
            right_ear = self._eye_aspect_ratio(landmarks[[33, 160, 158, 133, 153, 144]])
            scores['eyes_open_score'] = min(100, ((left_ear + right_ear) / 0.5) * 100)
            scores['smile_score'] = min(100, (self._mouth_aspect_ratio(landmarks[[61, 291, 0, 17, 37, 267, 84, 314, 405, 181, 13, 14]]) / 0.5) * 100)

            center_x = np.mean([lm.x for lm in main_face.landmark]) * w
            center_y = np.mean([lm.y for lm in main_face.landmark]) * h
            dist_to_third = min(abs(center_x - w/3), abs(center_x - 2*w/3), abs(center_y - h/3), abs(center_y - 2*h/3))
            scores['composition_score'] = max(0, 100 - (dist_to_third / (max(w, h) / 6)) * 100)
        return scores
