#!/usr/bin/env python3
# Licensed under GPLV3.0
# (c) 2025 Ernedin Zajko <ezajko@root.ba>

"""
Settings Repository Interface for PyRedactor Application

Abstract interface for settings management operations.
"""

from abc import ABC, abstractmethod
from typing import Optional

from ..entities.settings import SettingsEntity


class SettingsRepositoryInterface(ABC):
    """Abstract interface for settings repository operations"""
    
    @abstractmethod
    def load_settings(self) -> Optional[SettingsEntity]:
        """Load application settings"""
        pass
    
    @abstractmethod
    def save_settings(self, settings: SettingsEntity) -> bool:
        """Save application settings"""
        pass
    
    @abstractmethod
    def get_default_settings(self) -> SettingsEntity:
        """Get default application settings"""
        pass