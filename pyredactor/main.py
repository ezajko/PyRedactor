#!/usr/bin/env python3
# Licensed under GPLV3.0
# (c) 2025 Ernedin Zajko <ezajko@root.ba>

"""
Main application entry point for PyRedactor
"""

import sys
from PySide6.QtWidgets import QApplication

from .ui.main_window import MainWindow
from .application.di_container import DIContainer
from .infrastructure.persistence.file_system_repository import FileSystemDocumentRepository
from .core.interfaces.settings_repository import SettingsRepositoryInterface
from .ocr.tesseract_ocr_service import TesseractOCRService
from .core.entities.settings import SettingsEntity
from typing import Optional, List

# Create dummy implementations for missing services
class InMemorySettingsRepository(SettingsRepositoryInterface):
    def load_settings(self) -> Optional[SettingsEntity]:
        return SettingsEntity()
    def save_settings(self, settings: SettingsEntity) -> bool:
        return True
    def get_default_settings(self) -> SettingsEntity:
        return SettingsEntity()

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)

    # Setup DI
    di_container = DIContainer.get_instance()
    di_container.set_document_repository(FileSystemDocumentRepository())
    di_container.set_settings_repository(InMemorySettingsRepository())
    di_container.set_ocr_service(TesseractOCRService())

    document_service = di_container.get_document_management_service()
    redaction_service = di_container.get_redaction_service()
    settings_service = di_container.get_settings_management_service()

    window = MainWindow(
        document_service=document_service,
        redaction_service=redaction_service,
        settings_service=settings_service
    )
    window.show()

    # Run the application event loop
    exit_code = app.exec()

    # Clean up threads before exiting
    if hasattr(window, 'model_thread') and window.model_thread and window.model_thread.isRunning():
        window.model_thread.quit()
        window.model_thread.wait()

    # Clean up loader thread if it exists
    if hasattr(window, '_loader_thread') and window._loader_thread and window._loader_thread.isRunning():
        window._loader_thread.quit()
        window._loader_thread.wait()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
