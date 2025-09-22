"""
Unit Tests for PyRedactor Core Entities
"""

import pytest
from unittest.mock import Mock, patch
import uuid
from PIL import Image

from PyRedactor.pyredactor.core.entities.rectangle import RectangleEntity
from PyRedactor.pyredactor.core.entities.page import PageEntity
from PyRedactor.pyredactor.core.entities.document import DocumentEntity
from PyRedactor.pyredactor.core.entities.settings import SettingsEntity


class TestRectangleEntity:
    """Test cases for RectangleEntity"""
    
    def test_rectangle_creation(self):
        """Test rectangle creation with valid parameters"""
        rect_id = str(uuid.uuid4())
        start_point = (10, 20)
        end_point = (50, 60)
        color = "black"
        
        rectangle = RectangleEntity(rect_id, start_point, end_point, color)
        
        assert rectangle.id == rect_id
        assert rectangle.start_point == (10, 20)
        assert rectangle.end_point == (50, 60)
        assert rectangle.color == "black"
    
    def test_rectangle_normalization(self):
        """Test that rectangle coordinates are properly normalized"""
        rect_id = str(uuid.uuid4())
        # Create rectangle with reversed coordinates
        start_point = (50, 60)
        end_point = (10, 20)
        
        rectangle = RectangleEntity(rect_id, start_point, end_point, "red")
        
        # Should be normalized to proper order
        assert rectangle.start_point == (10, 20)
        assert rectangle.end_point == (50, 60)
    
    def test_rectangle_properties(self):
        """Test rectangle property calculations"""
        rect_id = str(uuid.uuid4())
        start_point = (10, 20)
        end_point = (50, 60)
        
        rectangle = RectangleEntity(rect_id, start_point, end_point, "black")
        
        assert rectangle.width == 40
        assert rectangle.height == 40
        assert rectangle.area == 1600
    
    def test_rectangle_move(self):
        """Test rectangle movement"""
        rect_id = str(uuid.uuid4())
        start_point = (10, 20)
        end_point = (50, 60)
        
        rectangle = RectangleEntity(rect_id, start_point, end_point, "black")
        moved_rectangle = rectangle.move(10, 15)
        
        assert moved_rectangle.start_point == (20, 35)
        assert moved_rectangle.end_point == (60, 75)
        assert moved_rectangle.color == "black"
    
    def test_rectangle_resize(self):
        """Test rectangle resizing"""
        rect_id = str(uuid.uuid4())
        start_point = (10, 20)
        end_point = (50, 60)
        
        rectangle = RectangleEntity(rect_id, start_point, end_point, "black")
        resized_rectangle = rectangle.resize(30, 40)
        
        assert resized_rectangle.start_point == (10, 20)
        assert resized_rectangle.end_point == (40, 60)  # 10+30, 20+40
        assert resized_rectangle.color == "black"
    
    def test_rectangle_change_color(self):
        """Test rectangle color change"""
        rect_id = str(uuid.uuid4())
        start_point = (10, 20)
        end_point = (50, 60)
        
        rectangle = RectangleEntity(rect_id, start_point, end_point, "black")
        colored_rectangle = rectangle.change_color("red")
        
        assert colored_rectangle.start_point == (10, 20)
        assert colored_rectangle.end_point == (50, 60)
        assert colored_rectangle.color == "red"


class TestPageEntity:
    """Test cases for PageEntity"""
    
    def test_page_creation(self):
        """Test page creation with valid parameters"""
        page = PageEntity()
        
        assert page.id is not None
        assert page.page_number == 0
        assert page.image is None
        assert page.rectangles == []
        assert page.size == (0, 0)
    
    def test_page_with_image(self):
        """Test page creation with image"""
        # Create a mock PIL image
        mock_image = Mock(spec=Image.Image)
        mock_image.size = (800, 600)
        
        page = PageEntity(
            page_number=1,
            image=mock_image,
            size=(800, 600)
        )
        
        assert page.page_number == 1
        assert page.image == mock_image
        assert page.size == (800, 600)
    
    def test_add_rectangle(self):
        """Test adding rectangles to page"""
        page = PageEntity()
        rectangle = RectangleEntity(str(uuid.uuid4()), (10, 20), (50, 60), "black")
        
        result = page.add_rectangle(rectangle)
        
        assert result is True
        assert len(page.rectangles) == 1
        assert page.rectangles[0] == rectangle
    
    def test_remove_rectangle(self):
        """Test removing rectangles from page"""
        page = PageEntity()
        rect_id = str(uuid.uuid4())
        rectangle = RectangleEntity(rect_id, (10, 20), (50, 60), "black")
        page.add_rectangle(rectangle)
        
        result = page.remove_rectangle(rect_id)
        
        assert result is True
        assert len(page.rectangles) == 0
    
    def test_remove_nonexistent_rectangle(self):
        """Test removing non-existent rectangle"""
        page = PageEntity()
        result = page.remove_rectangle("nonexistent_id")
        
        assert result is False
        assert len(page.rectangles) == 0
    
    def test_get_rectangle(self):
        """Test getting rectangle by ID"""
        page = PageEntity()
        rect_id = str(uuid.uuid4())
        rectangle = RectangleEntity(rect_id, (10, 20), (50, 60), "black")
        page.add_rectangle(rectangle)
        
        result = page.get_rectangle(rect_id)
        
        assert result == rectangle
    
    def test_clear_rectangles(self):
        """Test clearing all rectangles"""
        page = PageEntity()
        rectangle1 = RectangleEntity(str(uuid.uuid4()), (10, 20), (50, 60), "black")
        rectangle2 = RectangleEntity(str(uuid.uuid4()), (70, 80), (90, 100), "red")
        page.add_rectangle(rectangle1)
        page.add_rectangle(rectangle2)
        
        count = page.clear_rectangles()
        
        assert count == 2
        assert len(page.rectangles) == 0
    
    def test_rectangle_count(self):
        """Test rectangle counting"""
        page = PageEntity()
        assert page.rectangle_count == 0
        
        rectangle1 = RectangleEntity(str(uuid.uuid4()), (10, 20), (50, 60), "black")
        rectangle2 = RectangleEntity(str(uuid.uuid4()), (70, 80), (90, 100), "red")
        page.add_rectangle(rectangle1)
        page.add_rectangle(rectangle2)
        
        assert page.rectangle_count == 2


class TestDocumentEntity:
    """Test cases for DocumentEntity"""
    
    def test_document_creation(self):
        """Test document creation"""
        document = DocumentEntity()
        
        assert document.id is not None
        assert document.file_path == ""
        assert document.pages == []
        assert document.current_page_index == 0
        assert document.metadata == {}
    
    def test_document_with_file_path(self):
        """Test document creation with file path"""
        file_path = "/path/to/document.pdf"
        document = DocumentEntity(file_path=file_path)
        
        assert document.file_path == file_path
        assert document.title == "document"
    
    def test_add_page(self):
        """Test adding pages to document"""
        document = DocumentEntity()
        page = PageEntity()
        
        result = document.add_page(page)
        
        assert result is True
        assert len(document.pages) == 1
        assert document.pages[0] == page
    
    def test_remove_page(self):
        """Test removing pages from document"""
        document = DocumentEntity()
        page1 = PageEntity()
        page2 = PageEntity()
        document.add_page(page1)
        document.add_page(page2)
        
        result = document.remove_page(0)
        
        assert result is True
        assert len(document.pages) == 1
        assert document.pages[0] == page2
    
    def test_remove_invalid_page(self):
        """Test removing invalid page index"""
        document = DocumentEntity()
        result = document.remove_page(5)
        
        assert result is False
        assert len(document.pages) == 0
    
    def test_get_page(self):
        """Test getting page by index"""
        document = DocumentEntity()
        page = PageEntity()
        document.add_page(page)
        
        result = document.get_page(0)
        
        assert result == page
    
    def test_get_current_page(self):
        """Test getting current page"""
        document = DocumentEntity()
        page1 = PageEntity(page_number=1)
        page2 = PageEntity(page_number=2)
        document.add_page(page1)
        document.add_page(page2)
        document.current_page_index = 1
        
        result = document.get_current_page()
        
        assert result == page2
    
    def test_set_current_page(self):
        """Test setting current page"""
        document = DocumentEntity()
        page1 = PageEntity()
        page2 = PageEntity()
        document.add_page(page1)
        document.add_page(page2)
        
        result = document.set_current_page(1)
        
        assert result is True
        assert document.current_page_index == 1
    
    def test_set_invalid_current_page(self):
        """Test setting invalid current page"""
        document = DocumentEntity()
        page = PageEntity()
        document.add_page(page)
        
        result = document.set_current_page(5)
        
        assert result is False
        assert document.current_page_index == 0
    
    def test_navigation(self):
        """Test page navigation"""
        document = DocumentEntity()
        page1 = PageEntity()
        page2 = PageEntity()
        page3 = PageEntity()
        document.add_page(page1)
        document.add_page(page2)
        document.add_page(page3)
        
        # Navigate forward
        result1 = document.next_page()
        assert result1 is True
        assert document.current_page_index == 1
        
        result2 = document.next_page()
        assert result2 is True
        assert document.current_page_index == 2
        
        result3 = document.next_page()
        assert result3 is False  # Already at last page
        assert document.current_page_index == 2
        
        # Navigate backward
        result4 = document.previous_page()
        assert result4 is True
        assert document.current_page_index == 1
        
        result5 = document.previous_page()
        assert result5 is True
        assert document.current_page_index == 0
        
        result6 = document.previous_page()
        assert result6 is False  # Already at first page
        assert document.current_page_index == 0
    
    def test_page_count(self):
        """Test page counting"""
        document = DocumentEntity()
        assert document.page_count == 0
        
        page1 = PageEntity()
        page2 = PageEntity()
        document.add_page(page1)
        document.add_page(page2)
        
        assert document.page_count == 2
    
    def test_total_rectangles(self):
        """Test total rectangle counting across all pages"""
        document = DocumentEntity()
        page1 = PageEntity()
        page2 = PageEntity()
        document.add_page(page1)
        document.add_page(page2)
        
        # Add rectangles to pages
        rect1 = RectangleEntity(str(uuid.uuid4()), (10, 20), (50, 60), "black")
        rect2 = RectangleEntity(str(uuid.uuid4()), (70, 80), (90, 100), "red")
        page1.add_rectangle(rect1)
        page1.add_rectangle(rect2)
        
        rect3 = RectangleEntity(str(uuid.uuid4()), (30, 40), (70, 80), "green")
        page2.add_rectangle(rect3)
        
        assert document.total_rectangles == 3


class TestSettingsEntity:
    """Test cases for SettingsEntity"""
    
    def test_settings_creation(self):
        """Test settings creation with default values"""
        settings = SettingsEntity()
        
        assert settings.fill_color == "black"
        assert settings.output_quality == "ebook"
        assert settings.ocr_enabled is True
        assert settings.ocr_language == "eng"
        assert settings.history_length == 30
        assert settings.zoom_level == 100
        assert settings.ui_theme == "default"
        assert settings.last_opened_directory == ""
        assert settings.auto_save_work_files is True
    
    def test_settings_validation(self):
        """Test settings validation"""
        settings = SettingsEntity()
        assert settings.validate() is True
        
        # Test invalid fill color
        settings.fill_color = "invalid_color"
        assert settings.validate() is False
        
        # Reset and test invalid quality
        settings.fill_color = "black"
        settings.output_quality = "invalid_quality"
        assert settings.validate() is False
        
        # Reset and test invalid history length
        settings.output_quality = "ebook"
        settings.history_length = -5
        assert settings.validate() is False
        
        # Reset and test invalid zoom level
        settings.history_length = 30
        settings.zoom_level = 5  # Too low
        assert settings.validate() is False
        
        settings.zoom_level = 500  # Too high
        assert settings.validate() is False
        
        # Reset and test valid settings
        settings.zoom_level = 100
        assert settings.validate() is True
    
    def test_settings_serialization(self):
        """Test settings serialization"""
        settings = SettingsEntity(
            fill_color="red",
            output_quality="printer",
            ocr_enabled=False,
            ocr_language="fra",
            history_length=50,
            zoom_level=150,
            ui_theme="dark",
            last_opened_directory="/home/user/Documents",
            auto_save_work_files=False
        )
        
        # Test to_dict
        data = settings.to_dict()
        assert data["fill_color"] == "red"
        assert data["output_quality"] == "printer"
        assert data["ocr_enabled"] is False
        assert data["ocr_language"] == "fra"
        assert data["history_length"] == 50
        assert data["zoom_level"] == 150
        assert data["ui_theme"] == "dark"
        assert data["last_opened_directory"] == "/home/user/Documents"
        assert data["auto_save_work_files"] is False
        
        # Test from_dict
        new_settings = SettingsEntity.from_dict(data)
        assert new_settings.fill_color == "red"
        assert new_settings.output_quality == "printer"
        assert new_settings.ocr_enabled is False
        assert new_settings.ocr_language == "fra"
        assert new_settings.history_length == 50
        assert new_settings.zoom_level == 150
        assert new_settings.ui_theme == "dark"
        assert new_settings.last_opened_directory == "/home/user/Documents"
        assert new_settings.auto_save_work_files is False