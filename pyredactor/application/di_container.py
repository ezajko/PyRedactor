#!/usr/bin/env python3
# Licensed under GPLV3.0
# (c) 2025 Ernedin Zajko <ezajko@root.ba>

"""
Dependency Injection Container for PyRedactor Application

Manages application dependencies and wiring.
"""

from typing import Optional

# Core services
from ..core.services.document_management import DocumentManagementService
from ..core.services.redaction import RedactionService
from ..core.services.settings import SettingsManagementService

# Core interfaces
from ..core.interfaces.document_repository import DocumentRepositoryInterface
from ..core.interfaces.settings_repository import SettingsRepositoryInterface
from ..core.interfaces.ocr_service import OCRServiceInterface

# Infrastructure implementations (will be created later)
# For now, we'll use the existing implementations


class DIContainer:
    """Dependency injection container"""
    
    _instance: Optional['DIContainer'] = None
    
    def __init__(self):
        self._document_management_service: Optional[DocumentManagementService] = None
        self._redaction_service: Optional[RedactionService] = None
        self._settings_management_service: Optional[SettingsManagementService] = None
        
        # Repositories and services will be injected later
        self._document_repository: Optional[DocumentRepositoryInterface] = None
        self._settings_repository: Optional[SettingsRepositoryInterface] = None
        self._ocr_service: Optional[OCRServiceInterface] = None
    
    @classmethod
    def get_instance(cls) -> 'DIContainer':
        """Get singleton instance of DI container"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def set_document_repository(self, repository: DocumentRepositoryInterface) -> None:
        """Set document repository implementation"""
        self._document_repository = repository
    
    def set_settings_repository(self, repository: SettingsRepositoryInterface) -> None:
        """Set settings repository implementation"""
        self._settings_repository = repository
    
    def set_ocr_service(self, service: OCRServiceInterface) -> None:
        """Set OCR service implementation"""
        self._ocr_service = service
    
    def get_document_management_service(self) -> DocumentManagementService:
        """Get document management service with dependencies"""
        if self._document_management_service is None:
            if self._document_repository is None or self._ocr_service is None:
                raise RuntimeError("Document repository and OCR service must be set before getting DocumentManagementService")
            self._document_management_service = DocumentManagementService(self._document_repository, self._ocr_service)
        return self._document_management_service
    
    def get_redaction_service(self) -> RedactionService:
        """Get redaction service"""
        if self._redaction_service is None:
            self._redaction_service = RedactionService()
        return self._redaction_service
    
    def get_settings_management_service(self) -> SettingsManagementService:
        """Get settings management service with dependencies"""
        if self._settings_management_service is None:
            if self._settings_repository is None:
                raise RuntimeError("Settings repository must be set before getting SettingsManagementService")
            self._settings_management_service = SettingsManagementService(self._settings_repository)
        return self._settings_management_service