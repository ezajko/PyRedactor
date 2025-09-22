#!/usr/bin/env python3
# Licensed under GPLV3.0
# (c) 2025 Ernedin Zajko <ezajko@root.ba>

"""
Page Entity for PyRedactor Application

Represents a single page in a document with redaction rectangles.
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass, field
from PIL import Image
import uuid

from .rectangle import RectangleEntity


@dataclass
class PageEntity:
    """Entity representing a document page"""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    page_number: int = 0
    image: Optional[Image.Image] = None
    rectangles: List[RectangleEntity] = field(default_factory=list)
    size: Tuple[int, int] = (0, 0)
    
    def add_rectangle(self, rectangle: RectangleEntity) -> bool:
        """Add a rectangle to the page"""
        self.rectangles.append(rectangle)
        return True
    
    def remove_rectangle(self, rectangle_id: str) -> bool:
        """Remove a rectangle by ID"""
        for i, rect in enumerate(self.rectangles):
            if rect.id == rectangle_id:
                del self.rectangles[i]
                return True
        return False
    
    def get_rectangle(self, rectangle_id: str) -> Optional[RectangleEntity]:
        """Get a rectangle by ID"""
        for rect in self.rectangles:
            if rect.id == rectangle_id:
                return rect
        return None
    
    def clear_rectangles(self) -> int:
        """Clear all rectangles and return count of removed rectangles"""
        count = len(self.rectangles)
        self.rectangles.clear()
        return count
    
    def get_rectangles_by_area(self, min_area: float = 0) -> List[RectangleEntity]:
        """Get rectangles filtered by minimum area"""
        return [rect for rect in self.rectangles if rect.area >= min_area]
    
    @property
    def rectangle_count(self) -> int:
        """Get count of rectangles on this page"""
        return len(self.rectangles)

    def undo_last_rectangle(self) -> bool:
        """Removes the last added rectangle."""
        if self.rectangles:
            self.rectangles.pop()
            return True
        return False