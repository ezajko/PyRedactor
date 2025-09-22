"""
Integration Tests for PyRedactor Application
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from PIL import Image
import io

from PyRedactor.pyredactor.core.entities.document import DocumentEntity
from PyRedactor.pyredactor.core.entities.page import PageEntity
from PyRedactor.pyredactor.core.entities.rectangle import RectangleEntity
from PyRedactor.pyredactor.core.entities.settings import SettingsEntity

from PyRedactor.pyredactor.core.services.document_management import DocumentManagementService
from PyRedactor.pyredactor.core.services.redaction import RedactionService
from PyRedactor.pyredactor.core.services.settings import SettingsManagementService

from PyRedactor.pyredactor.core.interfaces.document_repository import DocumentRepositoryInterface
from PyRedactor.pyredactor.core.interfaces.settings_repository import SettingsRepositoryInterface
from PyRedactor.pyredactor.core.interfaces.ocr_service import OCRServiceInterface


class TestDocumentManagementIntegration:
    """Integration tests for document management"""
    
    def test_document_lifecycle(self):
        """Test complete document lifecycle: create, modify, save"""
        mock_repo = Mock(spec=DocumentRepositoryInterface)
        mock_document = Mock(spec=DocumentEntity)
        mock_document.pages = []
        mock_repo.load_document.return_value = mock_document
        mock_repo.save_document.return_value = True
        mock_repo.export_document.return_value = True
        mock_repo.save_raw.return_value = True
        mock_ocr_service = Mock(spec=OCRServiceInterface)
        doc_service = DocumentManagementService(mock_repo, mock_ocr_service)
        
        doc_path = "/test/document.pdf"
        document = doc_service.load_document(doc_path)
        assert document is not None
        mock_repo.load_document.assert_called_once_with(doc_path)
        
        doc_service.navigate_next_page(document)
        
        save_path = "/test/saved_document.pdf"
        result = doc_service.save_document(document, save_path)
        assert result is True
        mock_repo.save_document.assert_called_with(document, save_path)
        
        export_path = "/test/exported_document.pdf"
        settings = {"quality": "ebook"}
        result = doc_service.export_document(document, export_path, settings)
        assert result is True
        mock_repo.save_raw.assert_called_once()
    
    def test_document_navigation(self):
        """Test document navigation integration"""
        mock_repo = Mock(spec=DocumentRepositoryInterface)
        mock_document = Mock(spec=DocumentEntity)
        mock_document.page_count = 5
        mock_document.current_page_index = 0
        mock_document.set_current_page.return_value = True
        mock_document.next_page.return_value = True
        mock_document.previous_page.return_value = True
        mock_repo.load_document.return_value = mock_document
        mock_ocr_service = Mock(spec=OCRServiceInterface)
        doc_service = DocumentManagementService(mock_repo, mock_ocr_service)
        
        document = doc_service.load_document("/test/document.pdf")
        
        result = doc_service.navigate_next_page(document)
        assert result is True
        mock_document.next_page.assert_called_once()
        
        result = doc_service.navigate_previous_page(document)
        assert result is True
        mock_document.previous_page.assert_called_once()
        
        result = doc_service.navigate_to_page(document, 2)
        assert result is True
        mock_document.set_current_page.assert_called_once_with(2)
    
    def test_multiple_document_handling(self):
        """Test handling multiple documents"""
        mock_repo = Mock(spec=DocumentRepositoryInterface)
        mock_document1 = Mock(spec=DocumentEntity)
        mock_document2 = Mock(spec=DocumentEntity)
        mock_repo.load_document.side_effect = [mock_document1, mock_document2]
        mock_ocr_service = Mock(spec=OCRServiceInterface)
        doc_service = DocumentManagementService(mock_repo, mock_ocr_service)
        
        doc1 = doc_service.load_document("/test/document1.pdf")
        assert doc1 is mock_document1
        assert doc_service.get_current_document() == mock_document1
        
        doc2 = doc_service.load_document("/test/document2.pdf")
        assert doc2 == mock_document2
        assert doc_service.get_current_document() == mock_document2


class TestRedactionIntegration:
    """Integration tests for redaction functionality"""
    
    def test_redaction_workflow(self):
        """Test complete redaction workflow"""
        redact_service = RedactionService()
        
        mock_page = Mock(spec=PageEntity)
        mock_page.rectangles = []
        mock_page.add_rectangle.return_value = True
        mock_page.remove_rectangle.return_value = True
        mock_page.clear_rectangles.return_value = 3
        
        result1 = redact_service.add_redaction_rectangle(
            mock_page, 
            (10, 20), 
            (50, 60), 
            "black"
        )
        assert result1 is True
        mock_page.add_rectangle.assert_called_once()
        
        result2 = redact_service.add_redaction_rectangle(
            mock_page, 
            (70, 80), 
            (90, 100), 
            "red"
        )
        assert result2 is True
        assert mock_page.add_rectangle.call_count == 2
        
        rectangle_id = "test_rect_id"
        result3 = redact_service.remove_redaction_rectangle(mock_page, rectangle_id)
        assert result3 is True
        mock_page.remove_rectangle.assert_called_once_with(rectangle_id)
        
        result4 = redact_service.clear_all_redactions(mock_page)
        assert result4 == 3
        mock_page.clear_rectangles.assert_called_once()
    
    def test_redaction_modification(self):
        """Test redaction modification operations"""
        redact_service = RedactionService()
        
        mock_page = Mock(spec=PageEntity)
        mock_rectangle = Mock(spec=RectangleEntity)
        mock_rectangle.move.return_value = Mock(spec=RectangleEntity)
        mock_rectangle.resize.return_value = Mock(spec=RectangleEntity)
        mock_rectangle.change_color.return_value = Mock(spec=RectangleEntity)
        mock_page.get_rectangle.return_value = mock_rectangle
        mock_page.add_rectangle.return_value = True
        mock_page.remove_rectangle.return_value = True
        
        rectangle_id = "test_rect_id"
        
        result1 = redact_service.move_redaction_rectangle(
            mock_page, 
            rectangle_id, 
            10, 
            15
        )
        assert result1 is True
        mock_page.get_rectangle.assert_called_once_with(rectangle_id)
        mock_rectangle.move.assert_called_once_with(10, 15)
        mock_page.remove_rectangle.assert_called_once_with(rectangle_id)
        mock_page.add_rectangle.assert_called_once()
        
        result2 = redact_service.resize_redaction_rectangle(
            mock_page, 
            rectangle_id, 
            30, 
            40
        )
        assert result2 is True
        assert mock_page.get_rectangle.call_count == 2
        mock_rectangle.resize.assert_called_once_with(30, 40)
        assert mock_page.remove_rectangle.call_count == 2
        assert mock_page.add_rectangle.call_count == 2
        
        result3 = redact_service.change_redaction_color(
            mock_page, 
            rectangle_id, 
            "blue"
        )
        assert result3 is True
        assert mock_page.get_rectangle.call_count == 3
        mock_rectangle.change_color.assert_called_once_with("blue")
        assert mock_page.remove_rectangle.call_count == 3
        assert mock_page.add_rectangle.call_count == 3


class TestSettingsIntegration:
    """Integration tests for settings management"""
    
    def test_settings_lifecycle(self):
        """Test complete settings lifecycle: load, modify, save"""
        mock_repo = Mock(spec=SettingsRepositoryInterface)
        mock_settings = Mock(spec=SettingsEntity)
        mock_settings.fill_color = "black"
        mock_settings.output_quality = "ebook"
        mock_settings.ocr_enabled = True
        mock_settings.ocr_language = "eng"
        mock_repo.load_settings.return_value = mock_settings
        mock_repo.save_settings.return_value = True
        mock_repo.get_default_settings.return_value = mock_settings
        
        settings_service = SettingsManagementService(mock_repo)
        
        settings = settings_service.load_settings()
        assert settings == mock_settings
        mock_repo.load_settings.assert_called_once()
        
        result1 = settings_service.update_setting(settings, "fill_color", "red")
        assert result1 is True
        assert settings.fill_color == "red"
        
        result2 = settings_service.update_setting(settings, "output_quality", "printer")
        assert result2 is True
        assert settings.output_quality == "printer"
        
        result3 = settings_service.update_setting(settings, "ocr_enabled", False)
        assert result3 is True
        assert settings.ocr_enabled is False
        
        result4 = settings_service.save_settings(settings)
        assert result4 is True
        mock_repo.save_settings.assert_called_once_with(settings)
        
        default_settings = settings_service.get_default_settings()
        assert default_settings == mock_settings
        mock_repo.get_default_settings.assert_called_once()
    
    def test_settings_validation(self):
        """Test settings validation integration"""
        mock_repo = Mock(spec=SettingsRepositoryInterface)
        mock_settings = Mock(spec=SettingsEntity)
        mock_settings.validate.return_value = True
        
        settings_service = SettingsManagementService(mock_repo)
        
        result = settings_service.validate_settings(mock_settings)
        assert result is True
        mock_settings.validate.assert_called_once()
        
        mock_settings.validate.return_value = False
        result = settings_service.validate_settings(mock_settings)
        assert result is False


class TestCompleteWorkflowIntegration:
    """Integration tests for complete application workflow"""
    
    def test_complete_redaction_workflow(self):
        """Test complete redaction workflow from start to finish"""
        mock_doc_repo = Mock(spec=DocumentRepositoryInterface)
        mock_settings_repo = Mock(spec=SettingsRepositoryInterface)
        mock_ocr_service = Mock(spec=OCRServiceInterface)
        
        mock_document = Mock(spec=DocumentEntity)
        mock_document.page_count = 3
        mock_document.current_page_index = 0
        mock_document.set_current_page.return_value = True
        mock_document.pages = []
        mock_page = Mock(spec=PageEntity)
        mock_page.rectangles = []
        mock_settings = Mock(spec=SettingsEntity)
        mock_settings.fill_color = "black"
        mock_settings.output_quality = "ebook"
        mock_settings.ocr_enabled = True
        mock_settings.ocr_language = "eng"
        
        mock_doc_repo.load_document.return_value = mock_document
        mock_doc_repo.save_document.return_value = True
        mock_doc_repo.export_document.return_value = True
        mock_doc_repo.save_raw.return_value = True
        mock_settings_repo.load_settings.return_value = mock_settings
        mock_settings_repo.save_settings.return_value = True
        mock_settings_repo.get_default_settings.return_value = mock_settings
        mock_document.get_page.return_value = mock_page
        mock_page.add_rectangle.return_value = True
        
        doc_service = DocumentManagementService(mock_doc_repo, mock_ocr_service)
        redact_service = RedactionService()
        settings_service = SettingsManagementService(mock_settings_repo)
        
        document = doc_service.load_document("/test/document.pdf")
        assert document is not None
        
        settings = settings_service.load_settings()
        assert settings is not None
        
        result = doc_service.navigate_to_page(document, 1)
        assert result is True
        
        page = document.get_page(1)
        result1 = redact_service.add_redaction_rectangle(
            page, 
            (100, 100), 
            (200, 200), 
            settings.fill_color
        )
        assert result1 is True
        
        result2 = redact_service.add_redaction_rectangle(
            page, 
            (300, 300), 
            (400, 400), 
            "red"
        )
        assert result2 is True
        
        result3 = doc_service.save_document(document, "/test/work_file.pyredactor")
        assert result3 is True
        mock_doc_repo.save_document.assert_called_once()
        
        export_settings = {
            "output_quality": settings.output_quality,
            "ocr_enabled": settings.ocr_enabled,
            "ocr_language": settings.ocr_language
        }
        result4 = doc_service.export_document(
            document, 
            "/test/final_document.Redacted.pdf", 
            export_settings
        )
        assert result4 is True
        mock_doc_repo.save_raw.assert_called_once()
        
        result5 = settings_service.save_settings(settings)
        assert result5 is True
        mock_settings_repo.save_settings.assert_called_once()
    
    def test_undo_redaction_workflow(self):
        """Test undo redaction workflow"""
        redact_service = RedactionService()
        
        page = PageEntity()
        
        redact_service.add_redaction_rectangle(page, (10, 10), (50, 50), "black")
        redact_service.add_redaction_rectangle(page, (60, 60), (90, 90), "red")
        
        assert page.rectangle_count == 2
        
        result = redact_service.undo_last_redaction(page)
        assert result is True
        assert page.rectangle_count == 1
        
        result = redact_service.undo_last_redaction(page)
        assert result is True
        assert page.rectangle_count == 0
        
        result = redact_service.undo_last_redaction(page)
        assert result is False
        assert page.rectangle_count == 0
