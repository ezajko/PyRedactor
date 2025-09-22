"""
Sample Data Fixtures for PyRedactor Testing
"""

import pytest
import tempfile
import os
from PIL import Image
import io
import uuid


@pytest.fixture
def sample_image():
    """Create a sample PIL image for testing"""
    # Create a simple 100x100 RGB image
    image = Image.new('RGB', (100, 100), color='white')
    return image


@pytest.fixture
def sample_image_with_content():
    """Create a sample PIL image with content for testing"""
    # Create a 200x200 RGB image with some content
    image = Image.new('RGB', (200, 200), color='white')
    
    # Add some content to make it more realistic
    from PIL import ImageDraw
    draw = ImageDraw.Draw(image)
    
    # Draw some shapes
    draw.rectangle([20, 20, 80, 80], fill='blue')
    draw.ellipse([120, 120, 180, 180], fill='red')
    draw.line([0, 0, 200, 200], fill='black', width=2)
    
    return image


@pytest.fixture
def sample_pdf_bytes():
    """Create sample PDF bytes for testing"""
    # This would create a simple PDF in memory
    # For now, we'll return empty bytes as a placeholder
    return b"%PDF-1.4\n%EOF\n"


@pytest.fixture
def sample_rectangles():
    """Create sample rectangles for testing"""
    from PyRedactor.pyredactor.core.entities.rectangle import RectangleEntity
    import uuid
    
    rectangles = []
    
    # Create sample rectangles
    rect1 = RectangleEntity(
        str(uuid.uuid4()),
        (10, 20),
        (50, 60),
        "black"
    )
    
    rect2 = RectangleEntity(
        str(uuid.uuid4()),
        (70, 80),
        (90, 100),
        "red"
    )
    
    rect3 = RectangleEntity(
        str(uuid.uuid4()),
        (110, 120),
        (150, 160),
        "green"
    )
    
    rectangles.extend([rect1, rect2, rect3])
    
    return rectangles


@pytest.fixture
def sample_document():
    """Create a sample document with pages for testing"""
    from PyRedactor.pyredactor.core.entities.document import DocumentEntity
    from PyRedactor.pyredactor.core.entities.page import PageEntity
    from PyRedactor.pyredactor.core.entities.rectangle import RectangleEntity
    import uuid
    
    # Create document
    document = DocumentEntity()
    document.file_path = "/test/sample_document.pdf"
    
    # Create sample pages
    page1 = PageEntity()
    page1.page_number = 1
    page1.image = Image.new('RGB', (800, 600), color='white')
    page1.size = (800, 600)
    
    page2 = PageEntity()
    page2.page_number = 2
    page2.image = Image.new('RGB', (800, 600), color='white')
    page2.size = (800, 600)
    
    # Add rectangles to pages
    rect1 = RectangleEntity(
        str(uuid.uuid4()),
        (100, 100),
        (200, 200),
        "black"
    )
    
    rect2 = RectangleEntity(
        str(uuid.uuid4()),
        (300, 300),
        (400, 400),
        "red"
    )
    
    page1.add_rectangle(rect1)
    page2.add_rectangle(rect2)
    
    # Add pages to document
    document.add_page(page1)
    document.add_page(page2)
    
    return document


@pytest.fixture
def sample_settings():
    """Create sample settings for testing"""
    from PyRedactor.pyredactor.core.entities.settings import SettingsEntity
    
    settings = SettingsEntity()
    settings.fill_color = "black"
    settings.output_quality = "ebook"
    settings.ocr_enabled = True
    settings.ocr_language = "eng"
    settings.history_length = 30
    settings.zoom_level = 100
    settings.ui_theme = "default"
    settings.last_opened_directory = "/home/user/Documents"
    settings.auto_save_work_files = True
    
    return settings


@pytest.fixture
def temp_pdf_file():
    """Create a temporary PDF file for testing"""
    # This would create a temporary PDF file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        temp_path = f.name
    
    # For now, we'll just return a path - actual PDF creation would happen here
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_image_file(sample_image):
    """Create a temporary image file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        temp_path = f.name
    
    # Save the sample image to the temporary file
    sample_image.save(temp_path, 'PNG')
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def sample_work_data():
    """Create sample work data for testing"""
    work_data = {
        "file_path": "/test/sample_document.pdf",
        "pages": 2,
        "current_page": 0,
        "fill_color": "black",
        "output_quality": "ebook",
        "ocr_lang": "eng",
        "ocr_enabled": True,
        "rectangles": [
            [
                [[100, 100], [200, 200], "black"]
            ],
            [
                [[300, 300], [400, 400], "red"]
            ]
        ]
    }
    
    return work_data