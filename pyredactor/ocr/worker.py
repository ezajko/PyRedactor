#!/usr/bin/env python3
# Licensed under GPLV3.0
# (c) 2025 Ernedin Zajko <ezajko@root.ba>

"""
OCR Worker for PyRedactor Application
"""

from PySide6.QtCore import QThread, Signal

import pytesseract


class OCRWorker(QThread):
    """Worker thread for OCR processing"""
    finished = Signal(object)  # Signal emitted when OCR is complete
    error = Signal(str)        # Signal emitted when an error occurs
    
    def __init__(self, image_container, image_quality, scale, ocr_enabled, ocr_lang):
        super().__init__()
        self.image_container = image_container
        self.image_quality = image_quality
        self.scale = scale
        self.ocr_enabled = ocr_enabled
        self.ocr_lang = ocr_lang
        
    def run(self):
        try:
            # Get the finalized image as a PIL Image object (not JPEG bytes)
            final_image = self.image_container.finalizedImage(format='PIL', image_quality=self.image_quality, scale=self.scale)
            # Convert to RGB mode if needed for pytesseract
            if final_image.mode != 'RGB':
                final_image = final_image.convert('RGB')
                
            if self.ocr_enabled:
                pdf_page = pytesseract.image_to_pdf_or_hocr(final_image, extension='pdf', lang=self.ocr_lang)
            else:
                pdf_page = pytesseract.image_to_pdf_or_hocr(final_image, extension='pdf')
                
            self.finished.emit(pdf_page)
        except Exception as e:
            self.error.emit(str(e))