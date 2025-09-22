#!/usr/bin/env python3
# Licensed under GPLV3.0
# (c) 2025 Ernedin Zajko <ezajko@root.ba>

"""
Settings Entity for PyRedactor Application

Represents application configuration and user preferences.
"""

from typing import Dict, Any
from dataclasses import dataclass, field


@dataclass
class SettingsEntity:
    """Entity representing application settings"""
    
    fill_color: str = "black"
    output_quality: str = "ebook"
    ocr_enabled: bool = True
    ocr_language: str = "eng"
    history_length: int = 30
    zoom_level: int = 100
    ui_theme: str = "default"
    last_opened_directory: str = ""
    auto_save_work_files: bool = True
    
    def validate(self) -> bool:
        """Validate settings values"""
        valid_colors = ["black", "white", "red", "green"]
        valid_qualities = ["screen", "ebook", "printer", "prepress"]
        
        if self.fill_color not in valid_colors:
            return False
            
        if self.output_quality not in valid_qualities:
            return False
            
        if not isinstance(self.ocr_enabled, bool):
            return False
            
        if not isinstance(self.history_length, int) or self.history_length < 0:
            return False
            
        if not isinstance(self.zoom_level, int) or self.zoom_level < 10 or self.zoom_level > 400:
            return False
            
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary for serialization"""
        return {
            "fill_color": self.fill_color,
            "output_quality": self.output_quality,
            "ocr_enabled": self.ocr_enabled,
            "ocr_language": self.ocr_language,
            "history_length": self.history_length,
            "zoom_level": self.zoom_level,
            "ui_theme": self.ui_theme,
            "last_opened_directory": self.last_opened_directory,
            "auto_save_work_files": self.auto_save_work_files
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SettingsEntity':
        """Create settings from dictionary"""
        settings = cls()
        for key, value in data.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        return settings