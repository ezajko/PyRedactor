#!/usr/bin/env python3
# Licensed under GPLV3.0
# (c) 2025 Ernedin Zajko <ezajko@root.ba>

"""
Tesseract OCR Service for PyRedactor Application
"""

from typing import Optional, List
import pytesseract
from PIL import Image, ImageDraw
import io

from ..core.interfaces.ocr_service import OCRServiceInterface
from ..core.entities.page import PageEntity

class TesseractOCRService(OCRServiceInterface):
    """Tesseract implementation of the OCR service"""

    def process_page(self, page: PageEntity, lang: str, enabled: bool, quality: str = "ebook") -> Optional[bytes]:
        """Process a page with OCR and return PDF bytes"""
        try:
            final_image = self._draw_rectangles(page)
            if final_image.mode != 'RGB':
                final_image = final_image.convert('RGB')

            # Resize based on quality
            final_image = self._resize_for_quality(final_image, quality)

            if enabled:
                # OCR Enabled
                pdf_page = pytesseract.image_to_pdf_or_hocr(final_image, extension='pdf', lang=lang)
            else:
                # OCR Disabled - Direct PDF export
                buffer = io.BytesIO()
                
                # Determine compression based on quality
                save_quality = 75
                if quality == "screen": save_quality = 60
                elif quality == "printer": save_quality = 85
                elif quality == "prepress": save_quality = 95
                
                # Set resolution metadata (does not affect pixel data, but useful for viewers)
                dpi = 150
                if quality == "screen": dpi = 96
                elif quality == "printer": dpi = 300
                
                final_image.save(buffer, format='PDF', resolution=float(dpi), quality=save_quality, optimize=True)
                pdf_page = buffer.getvalue()

            return pdf_page
        except Exception as e:
            print(f"Error processing page with OCR: {e}")
            return None

    def _resize_for_quality(self, image: Image.Image, quality: str) -> Image.Image:
        """Resize image based on quality setting"""
        # Define max dimensions (approximate)
        # screen: ~72-96 DPI (A4 ~ 800x1100)
        # ebook: ~150 DPI (A4 ~ 1240x1754)
        # printer: ~300 DPI (A4 ~ 2480x3508)
        # prepress: Original or high DPI
        
        target_dpi = 150
        if quality == "screen": target_dpi = 96
        elif quality == "printer": target_dpi = 300
        elif quality == "prepress": return image # No resize
        
        w, h = image.size
        current_max = max(w, h)
        
        # A4 height in inches is ~11.7
        target_max = int(11.7 * target_dpi)
        
        if current_max > target_max:
            ratio = target_max / current_max
            new_size = (int(w * ratio), int(h * ratio))
            return image.resize(new_size, Image.Resampling.LANCZOS)
            
        return image

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
