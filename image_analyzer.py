
import imagehash
from PIL import Image
import os

class ImageAnalyzer:
    def get_basic_info(self, image_path):
        """Gets basic file info like size and dimensions."""
        try:
            stat = os.stat(image_path)
            size_mb = stat.st_size / (1024 * 1024)

            with Image.open(image_path) as img:
                width, height = img.size

            return {
                "size_mb": f"{size_mb:.2f} MB",
                "dimensions": f"{width}x{height}"
            }
        except Exception as e:
            print(f"Error getting basic info for {image_path}: {e}")
            return {}

    def get_exif(self, image_path):
        """Extracts basic EXIF data."""
        try:
            with Image.open(image_path) as img:
                exif_data = img._getexif()
                if not exif_data:
                    return {}

                FNUMBER = 33437
                EXPOSURE_TIME = 33434
                ISO_SPEED_RATINGS = 34855

                f_number = exif_data.get(FNUMBER)
                exposure_time = exif_data.get(EXPOSURE_TIME)
                iso = exif_data.get(ISO_SPEED_RATINGS)

                shutter_speed = "N/A"
                if exposure_time:
                    if exposure_time < 1:
                        shutter_speed = f"1/{int(1/exposure_time)}"
                    else:
                        shutter_speed = f"{int(exposure_time)}s"

                return {
                    'aperture': f"f/{f_number}" if f_number else "N/A",
                    'shutter_speed': shutter_speed,
                    'iso': iso if iso else "N/A"
                }
        except Exception as e:
            print(f"Error reading EXIF for {image_path}: {e}")
            return {}

    def get_hash(self, image_path):
        """Computes the average hash of an image."""
        try:
            with Image.open(image_path) as img:
                return imagehash.average_hash(img)
        except Exception as e:
            print(f"Error hashing {image_path}: {e}")
            return None
