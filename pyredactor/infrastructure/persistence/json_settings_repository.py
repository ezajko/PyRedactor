#!/usr/bin/env python3
# Licensed under GPLV3.0
# (c) 2025 Ernedin Zajko <ezajko@root.ba>

"""
JSON Settings Repository Implementation
"""

import json
import os
from typing import Optional
from ...core.interfaces.settings_repository import SettingsRepositoryInterface
from ...core.entities.settings import SettingsEntity

class JsonSettingsRepository(SettingsRepositoryInterface):
    def __init__(self, file_path: str = None):
        if file_path is None:
            config_dir = os.path.expanduser("~/.config/pyredactor")
            os.makedirs(config_dir, exist_ok=True)
            self.file_path = os.path.join(config_dir, "settings.json")
        else:
            self.file_path = file_path

    def load_settings(self) -> Optional[SettingsEntity]:
        if not os.path.exists(self.file_path):
            return self.get_default_settings()
        
        try:
            with open(self.file_path, 'r') as f:
                data = json.load(f)
            return SettingsEntity.from_dict(data)
        except Exception as e:
            print(f"Error loading settings: {e}")
            return self.get_default_settings()

    def save_settings(self, settings: SettingsEntity) -> bool:
        try:
            with open(self.file_path, 'w') as f:
                json.dump(settings.to_dict(), f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False

    def get_default_settings(self) -> SettingsEntity:
        return SettingsEntity()
