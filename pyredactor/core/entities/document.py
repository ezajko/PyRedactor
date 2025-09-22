#!/usr/bin/env python3
# Licensed under GPLV3.0
# (c) 2025 Ernedin Zajko <ezajko@root.ba>

"""
Document Entity for PyRedactor Application

Represents a complete document with multiple pages.
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass, field
import uuid
import os

from .page import PageEntity


@dataclass
class DocumentEntity:
    """Entity representing a complete document"""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    file_path: str = ""
    pages: List[PageEntity] = field(default_factory=list)
    current_page_index: int = 0
    metadata: dict = field(default_factory=dict)
    
    def add_page(self, page: PageEntity) -> bool:
        """Add a page to the document"""
        self.pages.append(page)
        return True
    
    def remove_page(self, page_index: int) -> bool:
        """Remove a page by index"""
        if 0 <= page_index < len(self.pages):
            del self.pages[page_index]
            # Adjust current page index if needed
            if self.current_page_index >= len(self.pages):
                self.current_page_index = max(0, len(self.pages) - 1)
            return True
        return False
    
    def get_page(self, page_index: int) -> Optional[PageEntity]:
        """Get a page by index"""
        if 0 <= page_index < len(self.pages):
            return self.pages[page_index]
        return None
    
    def get_current_page(self) -> Optional[PageEntity]:
        """Get the current page"""
        return self.get_page(self.current_page_index)
    
    def set_current_page(self, page_index: int) -> bool:
        """Set the current page index"""
        if 0 <= page_index < len(self.pages):
            self.current_page_index = page_index
            return True
        return False
    
    def next_page(self) -> bool:
        """Navigate to next page"""
        if self.current_page_index < len(self.pages) - 1:
            self.current_page_index += 1
            return True
        return False
    
    def previous_page(self) -> bool:
        """Navigate to previous page"""
        if self.current_page_index > 0:
            self.current_page_index -= 1
            return True
        return False
    
    @property
    def page_count(self) -> int:
        """Get total page count"""
        return len(self.pages)
    
    @property
    def title(self) -> str:
        """Get document title (filename without extension)"""
        if self.file_path:
            return os.path.splitext(os.path.basename(self.file_path))[0]
        return "Untitled Document"
    
    @property
    def total_rectangles(self) -> int:
        """Get total rectangle count across all pages"""
        return sum(page.rectangle_count for page in self.pages)