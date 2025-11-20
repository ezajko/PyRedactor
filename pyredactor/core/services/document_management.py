#!/usr/bin/env python3
# Licensed under GPLV3.0
# (c) 2025 Ernedin Zajko <ezajko@root.ba>

"""
Document Management Service
"""

from typing import Optional, List
import os
import copy
from ..interfaces.document_repository import DocumentRepositoryInterface
from ..entities.document import DocumentEntity
from ..entities.page import PageEntity
from ..interfaces.ocr_service import OCRServiceInterface
from PIL import Image


class DocumentManagementService:
    def __init__(self, document_repository: DocumentRepositoryInterface, ocr_service: OCRServiceInterface):
        self.document_repository = document_repository
        self.ocr_service = ocr_service
        self._current_document: Optional[DocumentEntity] = None
        self.undo_stack = []

    def load_document(self, file_path: str, progress_callback=None) -> Optional[DocumentEntity]:
        """
        Load a document from the file system.
        """
        self._current_document = self.document_repository.load_document(file_path, progress_callback)
        self.undo_stack = [] # Clear undo stack on new document
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
        
    def push_undo_state(self, page_index: int):
        """Save current state of a page for undo"""
        document = self.get_current_document()
        if document and 0 <= page_index < len(document.pages):
            page = document.pages[page_index]
            
            # Deep copy rectangles
            rectangles_copy = copy.deepcopy(page.rectangles)
            
            # Copy image (PIL images are mutable, so copy is needed)
            image_copy = page.image.copy() if page.image else None
            
            state = {
                'page_index': page_index,
                'image': image_copy,
                'rectangles': rectangles_copy
            }
            
            self.undo_stack.append(state)
            
            # Limit stack size
            if len(self.undo_stack) > 10:
                self.undo_stack.pop(0)

    def undo(self) -> Optional[int]:
        """Restore last state. Returns page_index of restored page or None."""
        if not self.undo_stack:
            return None
            
        state = self.undo_stack.pop()
        page_index = state['page_index']
        
        document = self.get_current_document()
        if document and 0 <= page_index < len(document.pages):
            page = document.pages[page_index]
            page.image = state['image']
            page.rectangles = state['rectangles']
            return page_index
            
        return None

    def rotate_page(self, document: DocumentEntity, page_index: int, angle: float):
        """
        Rotate the specified page by the given angle (degrees clockwise).
        Updates the page image and clears existing redactions on that page.
        """
        if 0 <= page_index < len(document.pages):
            # Push undo state before modification
            self.push_undo_state(page_index)
            
            page = document.pages[page_index]
            if page.image:
                page.image = page.image.rotate(angle, expand=True, fillcolor="white")
                page.rectangles.clear()
                return True
        return False

    def crop_page(self, document: DocumentEntity, page_index: int, x: int, y: int, width: int, height: int):
        """
        Crop the specified page to the given rectangle.
        If the cropped aspect ratio matches A4, upscale to standard A4 size (300 DPI).
        """
        if 0 <= page_index < len(document.pages):
            # Push undo state before modification
            self.push_undo_state(page_index)
            
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
                        cropped_img = page.image.crop((x, y, x + width, y + height))
                        
                        # Check aspect ratio for A4 resizing
                        ratio = width / height
                        a4_ratio = 2480 / 3508 # ~0.707
                        a4_landscape_ratio = 3508 / 2480 # ~1.414
                        
                        print(f"DEBUG: Crop w={width}, h={height}, ratio={ratio:.4f}")
                        print(f"DEBUG: A4 Portrait diff={abs(ratio - a4_ratio):.4f}, A4 Landscape diff={abs(ratio - a4_landscape_ratio):.4f}")

                        target_size = None
                        
                        # Allow 5% tolerance for aspect ratio matching to account for manual drag imprecision
                        if abs(ratio - a4_ratio) < 0.05 * a4_ratio:
                             print("DEBUG: Detected A4 Portrait match. Upscaling...")
                             target_size = (2480, 3508)
                        elif abs(ratio - a4_landscape_ratio) < 0.05 * a4_landscape_ratio:
                             print("DEBUG: Detected A4 Landscape match. Upscaling...")
                             target_size = (3508, 2480)
                        else:
                             print("DEBUG: No A4 match detected.")
                        
                        if target_size:
                            # Use LANCZOS for high quality downscaling/upscaling
                            cropped_img = cropped_img.resize(target_size, Image.Resampling.LANCZOS)
                        
                        page.image = cropped_img
                        page.rectangles.clear()
                        return True
                    except Exception as e:
                        print(f"Crop failed with exception: {e}")
                        # If failed, pop the undo state we just pushed to avoid invalid state
                        if self.undo_stack:
                            self.undo_stack.pop()
        return False
