#!/usr/bin/env python3
# Licensed under GPLV3.0
# (c) 2025 Ernedin Zajko <ezajko@root.ba>

"""
Document Repository Interface for PyRedactor Application

Abstract interface for document loading, saving, and management operations.
"""

from abc import ABC, abstractmethod
from typing import Optional, List

from ..entities.document import DocumentEntity
from ..entities.page import PageEntity


class DocumentRepositoryInterface(ABC):
    """Abstract interface for document repository operations"""
    
    @abstractmethod
    def load_document(self, file_path: str) -> Optional[DocumentEntity]:
        """Load a document from file path"""
        pass
    
    @abstractmethod
    def save_document(self, document: DocumentEntity, file_path: str) -> bool:
        """Save a document to file path"""
        pass
    
    @abstractmethod
    def export_document(self, document: DocumentEntity, file_path: str, settings: dict) -> bool:
        """Export document with specified settings"""
        pass
    
    @abstractmethod
    def load_work_file(self, file_path: str) -> Optional[dict]:
        """Load work file data"""
        pass
    
    @abstractmethod
    def save_work_file(self, document: DocumentEntity, file_path: str, settings: dict) -> bool:
        """Save work file data"""
        pass

    @abstractmethod
    def save_raw(self, data: bytes, file_path: str) -> bool:
        """Save raw bytes to a file."""
        pass