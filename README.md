# SPAI - Smart Photo AI

SPAI is a native Windows desktop application designed to help you sort, rate, and select your photos with the power of Artificial Intelligence. It is built with Python and PyQt6 and is designed to work completely offline.

## Features

### AI Mode (Auto-Sorting)
-   **AI-Powered Scoring:** Automatically analyzes and rates your photos from 0 to 100 based on criteria such as sharpness, exposure, face detection (including eye openness and expression), and composition.
-   **Automatic Sorting:** Sorts photos into `Best` (score 80-100), `Good` (60-79), and `Reject` (0-59) folders.
-   **Copy or Move:** Choose to either copy or move the files to the destination folders.
-   **Export Results:** Saves a detailed report of the AI ratings in both `ratings.json` and `ratings.csv` files inside a `rated` folder.

### Manual Mode (AI-Assisted Culling)
-   **AI Score Display:** View the AI score and the reasons for the score for each photo.
-   **Keyboard Shortcuts:** Quickly sort your photos using intuitive keyboard shortcuts:
    -   `1`, `2`, `3`: Move to custom folders (`sortir_1`, `sortir_2`, `sortir_3`).
    -   `X`: Move to the `rejected` folder.
    -   `S`: Skip the current photo.
    -   `Z`: Undo the last move.
-   **Image Rotation:** Rotate your images left or right. The changes are saved while preserving the EXIF metadata.
-   **Duplicate Detection:** A "Similar" badge will appear if the application detects other photos with a similar hash.

## How to Run
1.  **Install Dependencies:**
    ```bash
    pip install PyQt6 opencv-python numpy imagehash Pillow mediapipe piexif
    ```
2.  **Run the application:**
    ```bash
    python main.py
    ```

## Folder Structure
The application will create the sorting folders (`Best`, `Good`, `Reject`, `sortir_1`, etc.) in the parent directory of your source image folder to keep your original folder clean.
