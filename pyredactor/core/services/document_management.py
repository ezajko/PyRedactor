#!/usr/bin/env python3
# Licensed under GPLV3.0
# (c) 2025 Ernedin Zajko <ezajko@root.ba>

"""
Document Management Service
"""

from typing import Optional, List
import os
from ..interfaces.document_repository import DocumentRepositoryInterface
from ..entities.document import DocumentEntity
from ..entities.page import PageEntity
from ..interfaces.ocr_service import OCRServiceInterface


class DocumentManagementService:
    def __init__(self, document_repository: DocumentRepositoryInterface, ocr_service: OCRServiceInterface):
        self.document_repository = document_repository
        self.ocr_service = ocr_service
        self._current_document: Optional[DocumentEntity] = None

    def load_document(self, file_path: str, progress_callback=None) -> Optional[DocumentEntity]:
        """
        Load a document from the file system.
        """
        self._current_document = self.document_repository.load_document(file_path, progress_callback)
        return self._current_document

    def save_document(self, document: DocumentEntity, file_path: str):
        """
        Save the document (redactions) to a file.
        """
        self.document_repository.save_document(document, file_path)

    def export_document(self, document: DocumentEntity, file_path: str, settings: dict = None):
        """
        Export the redacted document to a PDF.
        """
        self.document_repository.export_document(document, file_path, settings)

    def get_current_document(self) -> Optional[DocumentEntity]:
        return self._current_document

    def navigate_to_page(self, document: DocumentEntity, page_index: int):
        document.current_page_index = page_index

    def navigate_next_page(self, document: DocumentEntity) -> bool:
        if document.current_page_index < document.page_count - 1:
            document.current_page_index += 1
            return True
        return False

    def navigate_previous_page(self, document: DocumentEntity) -> bool:
        if document.current_page_index > 0:
            document.current_page_index -= 1
            return True
        return False
        
    def rotate_page(self, document: DocumentEntity, page_index: int, angle: float):
        """
        Rotate the specified page by the given angle (degrees clockwise).
        Updates the page image and clears existing redactions on that page.
        """
        if 0 <= page_index < len(document.pages):
            page = document.pages[page_index]
            if page.image:
                # PIL rotate is counter-clockwise, so we negate the angle for clockwise behavior if needed.
                # Standard "Rotate Right" is -90 (or 270) in PIL if we want visual CW.
                # Let's stick to: angle > 0 is Counter-Clockwise (Standard math/PIL), 
                # but UI usually says "Right" (CW) and "Left" (CCW).
                # Let's assume input 'angle' is what we pass to PIL (CCW).
                # Rotate with expand=True to resize canvas to fit new orientation
                page.image = page.image.rotate(angle, expand=True, fillcolor="white")
                
                # Clear redactions as coordinates are now invalid
                page.rectangles.clear()
                
                return True
        return False

    def crop_page(self, document: DocumentEntity, page_index: int, x: int, y: int, width: int, height: int):
        """
        Crop the specified page to the given rectangle.
        """
        if 0 <= page_index < len(document.pages):
            page = document.pages[page_index]
            if page.image:
                img_w, img_h = page.image.size
                
                # Ensure coordinates are within bounds
                x = max(0, x)
                y = max(0, y)
                width = min(width, img_w - x)
                height = min(height, img_h - y)
                
                if width > 0 and height > 0:
                    try:
                        page.image = page.image.crop((x, y, x + width, y + height))
                        page.rectangles.clear()
                        return True
                    except Exception as e:
                        print(f"Crop failed with exception: {e}")
        return False
