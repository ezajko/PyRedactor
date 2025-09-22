#!/usr/bin/env python3
# Licensed under GPLV3.0
# (c) 2025 Ernedin Zajko <ezajko@root.ba>

"""
Tesseract OCR Service for PyRedactor Application
"""

from typing import Optional, List
import pytesseract
from PIL import Image, ImageDraw

from ..core.interfaces.ocr_service import OCRServiceInterface
from ..core.entities.page import PageEntity

class TesseractOCRService(OCRServiceInterface):
    """Tesseract implementation of the OCR service"""

    def process_page(self, page: PageEntity, lang: str, enabled: bool) -> Optional[bytes]:
        """Process a page with OCR and return PDF bytes"""
        try:
            final_image = self._draw_rectangles(page)
            if final_image.mode != 'RGB':
                final_image = final_image.convert('RGB')
            
            if enabled:
                pdf_page = pytesseract.image_to_pdf_or_hocr(final_image, extension='pdf', lang=lang)
            else:
                pdf_page = pytesseract.image_to_pdf_or_hocr(final_image, extension='pdf')
            
            return pdf_page
        except Exception as e:
            print(f"Error processing page with OCR: {e}")
            return None

    def get_available_languages(self) -> List[str]:
        """Get list of available OCR languages"""
        try:
            return sorted(pytesseract.get_languages())
        except Exception as e:
            print(f"Error getting OCR languages: {e}")
            return []

    def is_language_available(self, lang: str) -> bool:
        """Check if a specific language is available"""
        return lang in self.get_available_languages()

    def _draw_rectangles(self, page: PageEntity) -> Image.Image:
        """Draw redaction rectangles on the page image"""
        image_copy = page.image.copy()
        draw = ImageDraw.Draw(image_copy)
        for rect in page.rectangles:
            draw.rectangle([rect.start_point, rect.end_point], fill=rect.color)
        return image_copy
