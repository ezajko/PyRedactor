# PyRedactor

PyRedactor is a powerful, open-source PDF redaction tool built with Python and PySide6 (Qt). It allows users to securely redact sensitive information from PDF documents by converting pages to images, applying redaction markers, and re-exporting as a flattened PDF.

## Features

*   **Visual Redaction**: Draw redaction rectangles directly on document pages.
*   **Secure Flattening**: Pages are converted to images, ensuring redacted content is completely removed and cannot be recovered.
*   **OCR Support**: Optional Optical Character Recognition (OCR) using Tesseract to make redacted PDFs searchable.
*   **Page Manipulation**: Rotate pages (Left, Right, Fine Rotation) and Crop pages.
*   **Smart Cropping**: Automatically upscales cropped areas to A4 standard size if the aspect ratio matches.
*   **Image Enhancement**: Adjust brightness, contrast, sharpness, and apply deskewing/denoising (requires `unpaper` on Linux).
*   **Undo/Redo**: Undo support for marker placement, rotation, and cropping.
*   **Customizable**: Change marker colors, export quality, and UI settings.

## Prerequisites

*   **Python 3.8** or higher
*   **Tesseract OCR** (for OCR functionality)

## Installation

### Linux (Ubuntu/Debian)

1.  **Install System Dependencies:**
    ```bash
    sudo apt update
    sudo apt install python3-pip python3-venv tesseract-ocr libtesseract-dev
    ```
    *Optional: Install `unpaper` for advanced image enhancement:*
    ```bash
    sudo apt install unpaper
    ```

2.  **Clone the Repository:**
    ```bash
    git clone https://github.com/yourusername/PyRedactor.git
    cd PyRedactor
    ```

3.  **Create a Virtual Environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

4.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Windows

1.  **Install Python:**
    Download and install Python from [python.org](https://www.python.org/downloads/). Ensure you check "Add Python to PATH" during installation.

2.  **Install Tesseract OCR:**
    *   Download the installer from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki).
    *   Run the installer.
    *   **Important:** Add the Tesseract installation directory (e.g., `C:\Program Files\Tesseract-OCR`) to your System **PATH** environment variable.
        *   *Search for "Edit the system environment variables" -> Environment Variables -> Path -> Edit -> New -> Paste the path.*

3.  **Clone or Download the Repository:**
    *   If you have Git installed: `git clone ...`
    *   Or download the ZIP and extract it.

4.  **Setup Virtual Environment (PowerShell):**
    ```powershell
    cd PyRedactor
    python -m venv venv
    .\venv\Scripts\Activate
    ```

5.  **Install Dependencies:**
    ```powershell
    pip install -r requirements.txt
    ```

## Usage

1.  **Activate the Virtual Environment** (if not already active).
2.  **Run the Application:**
    ```bash
    python -m pyredactor.main
    ```
3.  **Workflow:**
    *   **Open** a PDF document.
    *   **Navigate** pages using the list or toolbar buttons.
    *   **Draw** redaction markers on sensitive areas.
    *   **Rotate** or **Crop** pages if necessary.
    *   **Save** or **Export** the document. The output will be a new PDF with images flattened, making redactions permanent.

## Configuration

Settings are automatically saved to:
*   **Linux:** `~/.config/pyredactor/settings.json`
*   **Windows:** `C:\Users\<User>\.config\pyredactor\settings.json` (or similar)

## License

This project is licensed under the GPLv3 License. See the `LICENSE` file for details.

## Credits

*   **Ernedin Zajko** - *Initial Work*
