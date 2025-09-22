#!/usr/bin/env python3
# Licensed under GPLV3.0
# (c) 2025 Ernedin Zajko <ezajko@root.ba>

"""
Icon Utilities for PyRedactor Application
"""

from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt, QSize
from io import BytesIO
import os


def create_colorful_icon(icon_type, color=None):
    """
    Create a colorful icon for the toolbar
    
    Args:
        icon_type (str): Type of icon to create
        color (QColor, optional): Color for the icon
    
    Returns:
        QIcon: Created icon
    """
    # Create a pixmap for the icon
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    if icon_type == "open":
        # Blue folder icon
        painter.setBrush(QColor(65, 105, 225))  # Royal Blue
        painter.setPen(QPen(QColor(30, 60, 150), 1))
        painter.drawRect(5, 8, 22, 16)
        painter.setBrush(QColor(100, 149, 237))  # Cornflower Blue
        painter.drawRect(5, 8, 22, 6)
        painter.setBrush(QColor(255, 255, 255, 100))
        painter.drawRect(8, 11, 16, 2)
        
    elif icon_type == "save":
        # Green save icon
        painter.setBrush(QColor(34, 139, 34))  # Forest Green
        painter.setPen(QPen(QColor(0, 100, 0), 1))
        painter.drawRect(5, 5, 22, 22)
        painter.setBrush(QColor(50, 205, 50))  # Lime Green
        painter.drawRect(10, 1, 12, 8)
        # Save disk indicator
        painter.setBrush(QColor(255, 255, 255))
        painter.drawRect(12, 15, 8, 2)
        painter.drawRect(12, 19, 8, 2)
        painter.drawRect(12, 23, 8, 2)
        
    elif icon_type == "save_as":
        # Light green save as icon
        painter.setBrush(QColor(50, 205, 50))  # Lime Green
        painter.setPen(QPen(QColor(34, 139, 34), 1))
        painter.drawRect(5, 5, 22, 22)
        painter.setBrush(QColor(144, 238, 144))  # Light Green
        painter.drawRect(10, 1, 12, 8)
        # Arrow indicator for "save as"
        painter.setBrush(QColor(255, 255, 0))  # Yellow
        painter.setPen(QPen(QColor(200, 200, 0), 1))
        painter.drawEllipse(18, 18, 8, 8)
        painter.setPen(QPen(QColor(100, 100, 0), 2))
        painter.drawLine(20, 20, 24, 24)
        
    elif icon_type == "undo":
        # Orange undo icon
        painter.setBrush(QColor(255, 165, 0))  # Orange
        painter.setPen(QPen(QColor(200, 120, 0), 1))
        painter.drawEllipse(8, 8, 16, 16)
        # Arrow
        painter.setBrush(QColor(255, 140, 0))  # Darker Orange
        painter.drawPolygon([
            16, 12,
            20, 16,
            16, 20,
            16, 18,
            12, 18,
            12, 14,
            16, 14
        ])
        
    elif icon_type == "delete":
        # Red delete icon
        painter.setBrush(QColor(220, 20, 60))  # Crimson
        painter.setPen(QPen(QColor(180, 0, 0), 1))
        painter.drawRect(8, 8, 16, 16)
        # X mark
        painter.setPen(QPen(QColor(255, 255, 255), 3))
        painter.drawLine(12, 12, 20, 20)
        painter.drawLine(20, 12, 12, 20)
        
    elif icon_type == "prev_page":
        # Purple previous page icon
        painter.setBrush(QColor(147, 112, 219))  # Medium Purple
        painter.setPen(QPen(QColor(120, 80, 180), 1))
        # Book pages
        painter.drawRect(8, 8, 16, 16)
        painter.drawRect(10, 10, 12, 12)
        # Arrow
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawLine(18, 16, 12, 16)
        painter.drawLine(14, 14, 12, 16)
        painter.drawLine(14, 18, 12, 16)
        
    elif icon_type == "next_page":
        # Violet next page icon
        painter.setBrush(QColor(138, 43, 226))  # Blue Violet
        painter.setPen(QPen(QColor(100, 30, 180), 1))
        # Book pages
        painter.drawRect(8, 8, 16, 16)
        painter.drawRect(10, 10, 12, 12)
        # Arrow
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawLine(14, 16, 20, 16)
        painter.drawLine(18, 14, 20, 16)
        painter.drawLine(18, 18, 20, 16)
        
    elif icon_type == "zoom_in":
        # Blue zoom in icon
        painter.setBrush(QColor(30, 144, 255))  # Dodger Blue
        painter.setPen(QPen(QColor(0, 100, 200), 1))
        # Magnifying glass
        painter.drawEllipse(8, 8, 16, 16)
        painter.setBrush(QColor(255, 255, 255, 200))
        painter.drawEllipse(10, 10, 6, 6)
        # Handle
        painter.setBrush(QColor(30, 144, 255))
        painter.drawRect(20, 20, 6, 4)
        # Plus sign
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawLine(16, 14, 16, 18)
        painter.drawLine(14, 16, 18, 16)
        
    elif icon_type == "zoom_out":
        # Light blue zoom out icon
        painter.setBrush(QColor(100, 149, 237))  # Cornflower Blue
        painter.setPen(QPen(QColor(65, 105, 225), 1))
        # Magnifying glass
        painter.drawEllipse(8, 8, 16, 16)
        painter.setBrush(QColor(255, 255, 255, 200))
        painter.drawEllipse(10, 10, 6, 6)
        # Handle
        painter.setBrush(QColor(100, 149, 237))
        painter.drawRect(20, 20, 6, 4)
        # Minus sign
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawLine(14, 16, 18, 16)
        
    elif icon_type == "quit":
        # Dark red quit icon
        painter.setBrush(QColor(178, 34, 34))  # Fire Brick
        painter.setPen(QPen(QColor(120, 0, 0), 1))
        painter.drawRect(8, 8, 16, 16)
        # X mark
        painter.setPen(QPen(QColor(255, 255, 255), 3))
        painter.drawLine(12, 12, 20, 20)
        painter.drawLine(20, 12, 12, 20)
        
    elif icon_type == "about":
        # Teal about icon
        painter.setBrush(QColor(0, 128, 128))  # Teal
        painter.setPen(QPen(QColor(0, 100, 100), 1))
        painter.drawEllipse(8, 8, 16, 16)
        # i letter
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawLine(16, 12, 16, 20)
        painter.drawPoint(16, 10)
        
    else:
        # Default icon
        if color:
            painter.setBrush(color)
        else:
            painter.setBrush(QColor(100, 100, 100))
        painter.setPen(QPen(QColor(70, 70, 70), 1))
        painter.drawRect(8, 8, 16, 16)
    
    painter.end()
    
    icon = QIcon(pixmap)
    return icon


def get_icon_from_theme(icon_name, fallback_type=None):
    """
    Get an icon from the system theme, with a colorful fallback
    
    Args:
        icon_name (str): Name of the system icon
        fallback_type (str, optional): Type of fallback icon to create
    
    Returns:
        QIcon: System icon or fallback icon
    """
    icon = QIcon.fromTheme(icon_name)
    if icon.isNull() and fallback_type:
        icon = create_colorful_icon(fallback_type)
    elif icon.isNull():
        icon = create_colorful_icon("default")
    return icon