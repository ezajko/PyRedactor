#!/usr/bin/env python3
# Licensed under GPLV3.0
# (c) 2025 Ernedin Zajko <ezajko@root.ba>

"""
Document Management Services for PyRedactor Application

Handles document loading, saving, and navigation operations.
"""

from typing import Optional, Tuple
from ..interfaces.document_repository import DocumentRepositoryInterface
from ..entities.document import DocumentEntity
from ..entities.page import PageEntity


from ..interfaces.ocr_service import OCRServiceInterface
from PyPDF2 import PdfMerger
import io

class DocumentManagementService:
    """Service for document management operations"""
    
    def __init__(self, document_repository: DocumentRepositoryInterface, ocr_service: OCRServiceInterface):
        self.document_repository = document_repository
        self.ocr_service = ocr_service
        self._current_document: Optional[DocumentEntity] = None
    
    def load_document(self, file_path: str) -> Optional[DocumentEntity]:
        """Load document from file path"""
        document = self.document_repository.load_document(file_path)
        if document:
            self._current_document = document
        return document
    
    def save_document(self, document: DocumentEntity, file_path: str) -> bool:
        """Save document to file path"""
        return self.document_repository.save_document(document, file_path)
    
    def export_document(self, document: DocumentEntity, file_path: str, settings: dict) -> bool:
        """Export document with specified settings"""
        try:
            merger = PdfMerger()
            for page in document.pages:
                pdf_page = self.ocr_service.process_page(page, settings.get("ocr_lang", "eng"), settings.get("ocr_enabled", True))
                if pdf_page:
                    merger.append(io.BytesIO(pdf_page))
            
            output_stream = io.BytesIO()
            merger.write(output_stream)
            merger.close()
            
            return self.document_repository.save_raw(output_stream.getvalue(), file_path)
        except Exception as e:
            print(f"Error exporting document: {e}")
            return False
    
    def navigate_to_page(self, document: DocumentEntity, page_index: int) -> bool:
        """Navigate to specific page"""
        return document.set_current_page(page_index)
    
    def navigate_next_page(self, document: DocumentEntity) -> bool:
        """Navigate to next page"""
        return document.next_page()
    
    def navigate_previous_page(self, document: DocumentEntity) -> bool:
        """Navigate to previous page"""
        return document.previous_page()
    
    def get_current_document(self) -> Optional[DocumentEntity]:
        """Get current document"""
        return self._current_document
    
    def set_current_document(self, document: DocumentEntity) -> None:
        """Set current document"""
        self._current_document = document

    def save_work_file(self, document: DocumentEntity, file_path: str, settings: dict) -> bool:
        """Save work file to a specific path."""
        return self.document_repository.save_work_file(document, file_path, settings)