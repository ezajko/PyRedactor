#!/usr/bin/env python3
# Licensed under GPLV3.0
# (c) 2025 Ernedin Zajko <ezajko@root.ba>

"""
OCR Service Interface for PyRedactor Application

Abstract interface for OCR processing operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.page import PageEntity


class OCRServiceInterface(ABC):
    """Abstract interface for OCR service operations"""
    
    @abstractmethod
    def process_page(self, page: PageEntity, lang: str, enabled: bool) -> Optional[bytes]:
        """Process a page with OCR and return PDF bytes"""
        pass
    
    @abstractmethod
    def get_available_languages(self) -> List[str]:
        """Get list of available OCR languages"""
        pass
    
    @abstractmethod
    def is_language_available(self, lang: str) -> bool:
        """Check if a specific language is available"""
        pass