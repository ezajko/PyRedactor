"""
PyTest Configuration and Fixtures for PyRedactor Application
"""

import pytest
import tempfile
import os
from PIL import Image
import io


@pytest.fixture
def sample_image():
    """Create a sample PIL image for testing"""
    # Create a simple 100x100 RGB image
    image = Image.new('RGB', (100, 100), color='white')
    return image


@pytest.fixture
def sample_image_with_rectangles(sample_image):
    """Create a sample image with some rectangles for testing"""
    # This would be an ImageContainer with rectangles
    from PyRedactor.pyredactor.core.entities.page import PageEntity
    from PyRedactor.pyredactor.core.entities.rectangle import RectangleEntity
    import uuid
    
    page = PageEntity()
    page.image = sample_image
    page.size = sample_image.size
    
    # Add some sample rectangles
    rect1 = RectangleEntity(str(uuid.uuid4()), (10, 10), (50, 50), "black")
    rect2 = RectangleEntity(str(uuid.uuid4()), (60, 60), (90, 90), "red")
    
    page.add_rectangle(rect1)
    page.add_rectangle(rect2)
    
    return page


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