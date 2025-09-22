"""
Unit Tests for PyRedactor Services
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import uuid
from PIL import Image

from PyRedactor.pyredactor.core.services.document_management import DocumentManagementService
from PyRedactor.pyredactor.core.services.redaction import RedactionService
from PyRedactor.pyredactor.core.services.settings import SettingsManagementService

from PyRedactor.pyredactor.core.entities.document import DocumentEntity
from PyRedactor.pyredactor.core.entities.page import PageEntity
from PyRedactor.pyredactor.core.entities.rectangle import RectangleEntity
from PyRedactor.pyredactor.core.entities.settings import SettingsEntity

from PyRedactor.pyredactor.core.interfaces.document_repository import DocumentRepositoryInterface
from PyRedactor.pyredactor.core.interfaces.settings_repository import SettingsRepositoryInterface
from PyRedactor.pyredactor.core.interfaces.ocr_service import OCRServiceInterface


class TestRedactionService:
    """Test cases for RedactionService"""
    
    def test_redaction_creation(self):
        """Test redaction service creation"""
        service = RedactionService()
        
        assert service is not None
    
    def test_add_redaction_rectangle(self):
        """Test adding redaction rectangle"""
        service = RedactionService()
        mock_page = Mock(spec=PageEntity)
        mock_page.add_rectangle.return_value = True
        
        result = service.add_redaction_rectangle(
            mock_page, 
            (10, 20), 
            (50, 60), 
            "black"
        )
        
        assert result is True
        mock_page.add_rectangle.assert_called_once()
    
    def test_add_redaction_rectangle_failure(self):
        """Test failed redaction rectangle addition"""
        service = RedactionService()
        mock_page = Mock(spec=PageEntity)
        mock_page.add_rectangle.side_effect = Exception("Test error")
        
        result = service.add_redaction_rectangle(
            mock_page, 
            (10, 20), 
            (50, 60), 
            "black"
        )
        
        assert result is False
    
    def test_remove_redaction_rectangle(self):
        """Test removing redaction rectangle"""
        service = RedactionService()
        mock_page = Mock(spec=PageEntity)
        mock_page.remove_rectangle.return_value = True
        rectangle_id = str(uuid.uuid4())
        
        result = service.remove_redaction_rectangle(mock_page, rectangle_id)
        
        assert result is True
        mock_page.remove_rectangle.assert_called_once_with(rectangle_id)
    
    def test_clear_all_redactions(self):
        """Test clearing all redactions"""
        service = RedactionService()
        mock_page = Mock(spec=PageEntity)
        mock_page.clear_rectangles.return_value = 3
        
        result = service.clear_all_redactions(mock_page)
        
        assert result == 3
        mock_page.clear_rectangles.assert_called_once()
    
    def test_move_redaction_rectangle(self):
        """Test moving redaction rectangle"""
        service = RedactionService()
        mock_page = Mock(spec=PageEntity)
        mock_rectangle = Mock(spec=RectangleEntity)
        mock_rectangle.move.return_value = Mock(spec=RectangleEntity)
        mock_page.get_rectangle.return_value = mock_rectangle
        mock_page.add_rectangle.return_value = True
        rectangle_id = str(uuid.uuid4())
        
        result = service.move_redaction_rectangle(
            mock_page, 
            rectangle_id, 
            10, 
            15
        )
        
        assert result is True
        mock_page.get_rectangle.assert_called_once_with(rectangle_id)
        mock_rectangle.move.assert_called_once_with(10, 15)
        mock_page.remove_rectangle.assert_called_once_with(rectangle_id)
        mock_page.add_rectangle.assert_called_once()
    
    def test_move_nonexistent_rectangle(self):
        """Test moving nonexistent rectangle"""
        service = RedactionService()
        mock_page = Mock(spec=PageEntity)
        mock_page.get_rectangle.return_value = None
        rectangle_id = str(uuid.uuid4())
        
        result = service.move_redaction_rectangle(
            mock_page, 
            rectangle_id, 
            10, 
            15
        )
        
        assert result is False
        mock_page.get_rectangle.assert_called_once_with(rectangle_id)
    
    def test_resize_redaction_rectangle(self):
        """Test resizing redaction rectangle"""
        service = RedactionService()
        mock_page = Mock(spec=PageEntity)
        mock_rectangle = Mock(spec=RectangleEntity)
        mock_rectangle.resize.return_value = Mock(spec=RectangleEntity)
        mock_page.get_rectangle.return_value = mock_rectangle
        mock_page.add_rectangle.return_value = True
        rectangle_id = str(uuid.uuid4())
        
        result = service.resize_redaction_rectangle(
            mock_page, 
            rectangle_id, 
            30, 
            40
        )
        
        assert result is True
        mock_page.get_rectangle.assert_called_once_with(rectangle_id)
        mock_rectangle.resize.assert_called_once_with(30, 40)
        mock_page.remove_rectangle.assert_called_once_with(rectangle_id)
        mock_page.add_rectangle.assert_called_once()
    
    def test_resize_nonexistent_rectangle(self):
        """Test resizing nonexistent rectangle"""
        service = RedactionService()
        mock_page = Mock(spec=PageEntity)
        mock_page.get_rectangle.return_value = None
        rectangle_id = str(uuid.uuid4())
        
        result = service.resize_redaction_rectangle(
            mock_page, 
            rectangle_id, 
            30, 
            40
        )
        
        assert result is False
        mock_page.get_rectangle.assert_called_once_with(rectangle_id)
    
    def test_change_redaction_color(self):
        """Test changing redaction rectangle color"""
        service = RedactionService()
        mock_page = Mock(spec=PageEntity)
        mock_rectangle = Mock(spec=RectangleEntity)
        mock_rectangle.change_color.return_value = Mock(spec=RectangleEntity)
        mock_page.get_rectangle.return_value = mock_rectangle
        mock_page.add_rectangle.return_value = True
        rectangle_id = str(uuid.uuid4())
        
        result = service.change_redaction_color(
            mock_page, 
            rectangle_id, 
            "red"
        )
        
        assert result is True
        mock_page.get_rectangle.assert_called_once_with(rectangle_id)
        mock_rectangle.change_color.assert_called_once_with("red")
        mock_page.remove_rectangle.assert_called_once_with(rectangle_id)
        mock_page.add_rectangle.assert_called_once()
    
    def test_change_color_nonexistent_rectangle(self):
        """Test changing color of nonexistent rectangle"""
        service = RedactionService()
        mock_page = Mock(spec=PageEntity)
        mock_page.get_rectangle.return_value = None
        rectangle_id = str(uuid.uuid4())
        
        result = service.change_redaction_color(
            mock_page, 
            rectangle_id, 
            "red"
        )
        
        assert result is False
        mock_page.get_rectangle.assert_called_once_with(rectangle_id)


class TestSettingsManagementService:
    """Test cases for SettingsManagementService"""
    
    def test_settings_management_creation(self):
        """Test settings management service creation"""
        mock_repo = Mock(spec=SettingsRepositoryInterface)
        service = SettingsManagementService(mock_repo)
        
        assert service.settings_repository == mock_repo
    
    def test_load_settings_success(self):
        """Test successful settings loading"""
        mock_repo = Mock(spec=SettingsRepositoryInterface)
        mock_settings = Mock(spec=SettingsEntity)
        mock_repo.load_settings.return_value = mock_settings
        
        service = SettingsManagementService(mock_repo)
        result = service.load_settings()
        
        assert result == mock_settings
        mock_repo.load_settings.assert_called_once()
    
    def test_load_settings_failure(self):
        """Test failed settings loading"""
        mock_repo = Mock(spec=SettingsRepositoryInterface)
        mock_repo.load_settings.return_value = None
        
        service = SettingsManagementService(mock_repo)
        result = service.load_settings()
        
        assert result is None
        mock_repo.load_settings.assert_called_once()
    
    def test_save_settings(self):
        """Test settings saving"""
        mock_repo = Mock(spec=SettingsRepositoryInterface)
        mock_repo.save_settings.return_value = True
        mock_settings = Mock(spec=SettingsEntity)
        
        service = SettingsManagementService(mock_repo)
        result = service.save_settings(mock_settings)
        
        assert result is True
        mock_repo.save_settings.assert_called_once_with(mock_settings)
    
    def test_get_default_settings(self):
        """Test getting default settings"""
        mock_repo = Mock(spec=SettingsRepositoryInterface)
        mock_settings = Mock(spec=SettingsEntity)
        mock_repo.get_default_settings.return_value = mock_settings
        
        service = SettingsManagementService(mock_repo)
        result = service.get_default_settings()
        
        assert result == mock_settings
        mock_repo.get_default_settings.assert_called_once()
    
    def test_update_setting_success(self):
        """Test successful setting update"""
        mock_repo = Mock(spec=SettingsRepositoryInterface)
        mock_settings = Mock(spec=SettingsEntity)
        mock_settings.fill_color = "black"
        
        service = SettingsManagementService(mock_repo)
        result = service.update_setting(mock_settings, "fill_color", "red")
        
        assert result is True
        assert mock_settings.fill_color == "red"
    
    def test_update_setting_failure(self):
        """Test failed setting update"""
        mock_repo = Mock(spec=SettingsRepositoryInterface)
        mock_settings = Mock(spec=SettingsEntity)
        
        service = SettingsManagementService(mock_repo)
        result = service.update_setting(mock_settings, "invalid_attribute", "value")
        
        assert result is False
    
    def test_validate_settings(self):
        """Test settings validation"""
        mock_repo = Mock(spec=SettingsRepositoryInterface)
        mock_settings = Mock(spec=SettingsEntity)
        mock_settings.validate.return_value = True
        
        service = SettingsManagementService(mock_repo)
        result = service.validate_settings(mock_settings)
        
        assert result is True
        mock_settings.validate.assert_called_once()