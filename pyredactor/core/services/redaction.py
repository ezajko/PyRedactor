#!/usr/bin/env python3
# Licensed under GPLV3.0
# (c) 2025 Ernedin Zajko <ezajko@root.ba>

"""
Redaction Services for PyRedactor Application

Handles redaction rectangle operations on document pages.
"""

from typing import Optional, Tuple
from ..entities.document import DocumentEntity
from ..entities.page import PageEntity
from ..entities.rectangle import RectangleEntity
import uuid


class RedactionService:
    """Service for redaction operations"""
    
    def __init__(self):
        pass
    
    def add_redaction_rectangle(
        self, 
        page: PageEntity, 
        start_point: Tuple[float, float], 
        end_point: Tuple[float, float], 
        color: str = "black"
    ) -> bool:
        """Add a redaction rectangle to a page"""
        try:
            rectangle = RectangleEntity(
                id=str(uuid.uuid4()),
                start_point=start_point,
                end_point=end_point,
                color=color
            )
            return page.add_rectangle(rectangle)
        except Exception:
            return False
    
    def remove_redaction_rectangle(self, page: PageEntity, rectangle_id: str) -> bool:
        """Remove a redaction rectangle from a page"""
        return page.remove_rectangle(rectangle_id)
    
    def clear_all_redactions(self, page: PageEntity) -> int:
        """Clear all redactions from a page and return count of removed rectangles"""
        count = page.clear_rectangles()
        return count
    
    def move_redaction_rectangle(
        self, 
        page: PageEntity, 
        rectangle_id: str, 
        delta_x: float, 
        delta_y: float
    ) -> bool:
        """Move a redaction rectangle by delta values"""
        rectangle = page.get_rectangle(rectangle_id)
        if rectangle:
            moved_rectangle = rectangle.move(delta_x, delta_y)
            # Remove old rectangle and add moved one
            page.remove_rectangle(rectangle_id)
            return page.add_rectangle(moved_rectangle)
        return False
    
    def resize_redaction_rectangle(
        self, 
        page: PageEntity, 
        rectangle_id: str, 
        new_width: float, 
        new_height: float
    ) -> bool:
        """Resize a redaction rectangle"""
        rectangle = page.get_rectangle(rectangle_id)
        if rectangle:
            resized_rectangle = rectangle.resize(new_width, new_height)
            # Remove old rectangle and add resized one
            page.remove_rectangle(rectangle_id)
            return page.add_rectangle(resized_rectangle)
        return False
    
    def change_redaction_color(
        self, 
        page: PageEntity, 
        rectangle_id: str, 
        new_color: str
    ) -> bool:
        """Change the color of a redaction rectangle"""
        rectangle = page.get_rectangle(rectangle_id)
        if rectangle:
            colored_rectangle = rectangle.change_color(new_color)
            # Remove old rectangle and add recolored one
            page.remove_rectangle(rectangle_id)
            return page.add_rectangle(colored_rectangle)
        return False

    def undo_last_redaction(self, page: PageEntity) -> bool:
        """Undo the last redaction on a page."""
        return page.undo_last_rectangle()