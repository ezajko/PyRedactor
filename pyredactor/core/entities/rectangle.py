#!/usr/bin/env python3
# Licensed under GPLV3.0
# (c) 2025 Ernedin Zajko <ezajko@root.ba>

"""
Rectangle Entity for PyRedactor Application

Represents a redaction rectangle on a document page.
"""

from typing import Tuple, Union
from dataclasses import dataclass


@dataclass
class RectangleEntity:
    """Entity representing a redaction rectangle"""
    
    id: str
    start_point: Tuple[float, float]
    end_point: Tuple[float, float]
    color: str
    
    def __post_init__(self):
        """Validate and normalize rectangle coordinates"""
        # Ensure proper ordering (x1 >= x0, y1 >= y0)
        x0, y0 = self.start_point
        x1, y1 = self.end_point
        
        # Normalize coordinates
        left = min(x0, x1)
        right = max(x0, x1)
        top = min(y0, y1)
        bottom = max(y0, y1)
        
        self.start_point = (left, top)
        self.end_point = (right, bottom)
    
    @property
    def width(self) -> float:
        """Get rectangle width"""
        return abs(self.end_point[0] - self.start_point[0])
    
    @property
    def height(self) -> float:
        """Get rectangle height"""
        return abs(self.end_point[1] - self.start_point[1])
    
    @property
    def area(self) -> float:
        """Get rectangle area"""
        return self.width * self.height
    
    def move(self, delta_x: float, delta_y: float) -> 'RectangleEntity':
        """Move rectangle by delta values"""
        new_start = (self.start_point[0] + delta_x, self.start_point[1] + delta_y)
        new_end = (self.end_point[0] + delta_x, self.end_point[1] + delta_y)
        return RectangleEntity(self.id, new_start, new_end, self.color)
    
    def resize(self, new_width: float, new_height: float) -> 'RectangleEntity':
        """Resize rectangle to new dimensions while keeping top-left corner"""
        new_end = (self.start_point[0] + new_width, self.start_point[1] + new_height)
        return RectangleEntity(self.id, self.start_point, new_end, self.color)
    
    def change_color(self, new_color: str) -> 'RectangleEntity':
        """Change rectangle color"""
        return RectangleEntity(self.id, self.start_point, self.end_point, new_color)