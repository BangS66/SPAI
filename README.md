# SPAI - Smart Photo AI

SPAI is a modern, offline desktop application for Windows designed to intelligently sort, rate, and manage large collections of photos. It leverages local AI/ML libraries to analyze photos based on various quality metrics, helping you quickly identify the best shots and organize them efficiently.

## Features

- **100% Offline**: No internet connection or API keys required. All processing is done locally on your machine.
- **Modern & Responsive UI**: A clean and intuitive user interface built with PySide6.
- **AI-Powered Sorting**: Automatically rates photos from 0-100 based on:
    - **Sharpness**: Detects blurry images.
    - **Exposure**: Analyzes brightness and contrast.
    - **Noise**: Estimates the level of noise in the photo.
    - **Face Detection**: Analyzes facial expressions, detects smiles, and checks if eyes are open.
    - **Composition**: Applies the rule of thirds to evaluate photo composition.
- **Multiple Sorting Modes**:
    - **AI Mode**: Automatically sorts photos into `Best`, `Good`, and `Reject` folders. Choose between Copy or Move operations.
    - **Manual Mode**: A detailed view for manual sorting with keyboard shortcuts. Features AI score display, image rotation, and a "Similar" badge for duplicates. Choose between Copy or Move.
    - **Auto Sort by Filename**: Groups and sorts photos based on common patterns in filenames, with a confirmation step.
- **Copy & Move Operations**: Users can choose whether to copy files to the destination folders or move them, providing full control over the original files.
- **High Performance**: Utilizes multithreading to ensure the UI remains responsive, even when processing thousands of photos.
- **Broad Format Support**: Supports a wide range of image formats, including JPG, PNG, WEBP, BMP, TIFF, and common RAW formats (.cr2, .nef, .arw).

## Getting Started

### Prerequisites

- Python 3.8+
- Git

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd spai
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the required libraries:**
    ```bash
    pip install -r requirements.txt
    ```

### Running the Application

To run SPAI, execute the `main.py` script from within the `src` directory:

```bash
python src/main.py
```

## Technology Stack

- **Framework**: Python 3
- **UI**: PySide6
- **AI & Image Processing**:
    - **OpenCV**: For core image analysis.
    - **Mediapipe**: For offline face detection.
    - **ImageHash**: For detecting similar photos.
    - **Pillow**: For image manipulation.
    - **rawpy**: For decoding RAW images.
