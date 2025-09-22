#!/usr/bin/env python3
# Licensed under GPLV3.0
# (c) 2025 Ernedin Zajko <ezajko@root.ba>

"""
Settings Management Services for PyRedactor Application

Handles application settings operations.
"""

from typing import Optional
from ..interfaces.settings_repository import SettingsRepositoryInterface
from ..entities.settings import SettingsEntity


class SettingsManagementService:
    """Service for settings management operations"""
    
    def __init__(self, settings_repository: SettingsRepositoryInterface):
        self.settings_repository = settings_repository
    
    def load_settings(self) -> Optional[SettingsEntity]:
        """Load application settings"""
        return self.settings_repository.load_settings()
    
    def save_settings(self, settings: SettingsEntity) -> bool:
        """Save application settings"""
        return self.settings_repository.save_settings(settings)
    
    def get_default_settings(self) -> SettingsEntity:
        """Get default application settings"""
        return self.settings_repository.get_default_settings()
    
    def update_setting(self, settings: SettingsEntity, key: str, value) -> bool:
        """Update a specific setting"""
        if hasattr(settings, key):
            setattr(settings, key, value)
            return True
        return False
    
    def validate_settings(self, settings: SettingsEntity) -> bool:
        """Validate settings values"""
        return settings.validate()