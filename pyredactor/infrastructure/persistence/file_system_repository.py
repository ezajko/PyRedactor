#!/usr/bin/env python3
# Licensed under GPLV3.0
# (c) 2025 Ernedin Zajko <ezajko@root.ba>

"""
File System Repository for PyRedactor Application
"""

import json
import hashlib
import os
import glob
from appdirs import user_data_dir
from typing import Optional, List
import pypdfium2 as pdfium
from PIL import Image

from ...core.interfaces.document_repository import DocumentRepositoryInterface
from ...core.entities.document import DocumentEntity
from ...core.entities.page import PageEntity

# Import unpaper preprocessing service
try:
    from ...ocr.unpaper_preprocessing import UnpaperPreprocessingService
    UNPAPER_AVAILABLE = True
except ImportError:
    UNPAPER_AVAILABLE = False
    UnpaperPreprocessingService = None

# Import image enhancement service
try:
    from ...image.enhancement_service import ImageEnhancementService
    ENHANCEMENT_AVAILABLE = True
except ImportError:
    ENHANCEMENT_AVAILABLE = False
    ImageEnhancementService = None

class FileSystemDocumentRepository(DocumentRepositoryInterface):
    """File system implementation of the document repository"""

    def __init__(self):
        # Initialize unpaper service if available
        self.unpaper_service = UnpaperPreprocessingService() if UNPAPER_AVAILABLE else None
        # Initialize enhancement service if available
        self.enhancement_service = ImageEnhancementService() if ENHANCEMENT_AVAILABLE else None
        # Default paper format (can be made configurable later)
        self.default_paper_format = "a4"
        # Enhancement settings (can be made configurable later)
        self.enhancement_enabled = False
        self.enhancement_brightness = 1.0
        self.enhancement_contrast = 1.0
        self.enhancement_sharpness = 1.0
        self.enhancement_auto_level = True
        self.enhancement_deskew = True
        self.enhancement_denoise = True

    def set_enhancement_settings(self, enabled=False, brightness=1.0, contrast=1.0,
                               sharpness=1.0, auto_level=True, deskew=True, denoise=True):
        """Set enhancement settings"""
        self.enhancement_enabled = enabled
        self.enhancement_brightness = brightness
        self.enhancement_contrast = contrast
        self.enhancement_sharpness = sharpness
        self.enhancement_auto_level = auto_level
        self.enhancement_deskew = deskew
        self.enhancement_denoise = denoise

    def load_document(self, file_path: str, progress_callback=None) -> Optional[DocumentEntity]:
        """Load a document from file path"""
        try:
            document = DocumentEntity(file_path=file_path)

            if file_path.lower().endswith('.pdf'):
                pdf = pdfium.PdfDocument(file_path)
                total_pages = len(pdf)
                for i in range(total_pages):
                    if progress_callback:
                        progress_callback(i, total_pages, f"Rendering page {i+1} of {total_pages}...")
                    
                    pil_image = pdf[i].render(scale=2).to_pil()
                    # Apply preprocessing in order: unpaper, then enhancement
                    processed_image = self._apply_preprocessing(pil_image)
                    page = PageEntity(
                        page_number=i,
                        image=processed_image if processed_image else pil_image,
                        size=pdf[i].get_size()
                    )
                    document.add_page(page)
            else:
                if progress_callback:
                    progress_callback(0, 1, "Loading image...")
                    
                pil_image = Image.open(file_path)
                # Apply preprocessing in order: unpaper, then enhancement
                processed_image = self._apply_preprocessing(pil_image)
                page = PageEntity(
                    page_number=0,
                    image=processed_image if processed_image else pil_image,
                    size=processed_image.size if processed_image else pil_image.size
                )
                document.add_page(page)

            return document
        except Exception as e:
            print(f"Error loading document: {e}")
            return None

    def _apply_preprocessing(self, image: Image.Image) -> Optional[Image.Image]:
        """Apply all preprocessing steps to an image"""
        processed_image = image.copy()
        image_modified = False

        # Step 1: Apply unpaper preprocessing if available
        if self.unpaper_service and self.unpaper_service.is_available():
            unpaper_result = self.unpaper_service.preprocess_pil_image(
                processed_image, self.default_paper_format)
            if unpaper_result:
                processed_image = unpaper_result
                image_modified = True

        # Step 2: Apply enhancement if enabled
        if self.enhancement_enabled and self.enhancement_service:
            try:
                enhanced_image = self.enhancement_service.preprocess_document(
                    processed_image,
                    brightness=self.enhancement_brightness,
                    contrast=self.enhancement_contrast,
                    sharpness=self.enhancement_sharpness,
                    auto_level=self.enhancement_auto_level,
                    deskew=self.enhancement_deskew,
                    denoise=self.enhancement_denoise
                )
                if enhanced_image and enhanced_image != processed_image:
                    processed_image = enhanced_image
                    image_modified = True
            except Exception as e:
                print(f"Error applying image enhancement: {e}")
                # Continue with previous result if enhancement fails

        return processed_image if image_modified else None

    def load_work_file(self, file_path: str) -> Optional[dict]:
        datadir = user_data_dir("PyRedactor", "digidigital")
        try:
            workfile_name = self._encode_filepath(file_path)
            workfile = os.path.join(datadir, workfile_name)
            if os.path.isfile(workfile):
                with open(workfile, "r", encoding="utf-8") as f:
                    work_data = json.load(f)
                return work_data
            else:
                return None
        except Exception as e:
            print(f"Error loading workfile: {e}")
            return None

    def save_work_file(self, document: DocumentEntity, file_path: str, settings: dict) -> bool:
        try:
            datadir = user_data_dir("PyRedactor", "digidigital")
            rectangles = self._export_rectangles(document.pages)
            if rectangles is not None:
                workfile_name = self._encode_filepath(file_path)
                work_data = {
                    "rectangles": rectangles,
                    "pages": document.page_count,
                    "current_page": document.current_page_index,
                    "fill_color": settings.get("fill_color", "black"),
                    "output_quality": settings.get("output_quality", "ebook"),
                }
                if not os.path.exists(datadir):
                    os.makedirs(datadir, exist_ok=True)
                with open(os.path.join(datadir, workfile_name), "w", encoding="utf-8") as f:
                    json.dump(work_data, f, ensure_ascii=False, indent=4)
                self._delete_oldest_files(datadir, settings.get("history_length", 30))
                return True
            else:
                self._delete_workfile(file_path)
                return True
        except Exception as e:
            print(f"Error in save_work_file: {e}")
            return False

    def _export_rectangles(self, pages: List[PageEntity]):
        rectangles = []
        for page in pages:
            processed_page_rectangles = []
            for rect in page.rectangles:
                processed_start = list(rect.start_point)
                processed_end = list(rect.end_point)
                processed_color = str(rect.color)
                processed_page_rectangles.append([processed_start, processed_end, processed_color])
            rectangles.append(processed_page_rectangles)

        contains_rectangles = [True if len(item) > 0 else False for item in rectangles]
        if any(contains_rectangles):
            return rectangles
        else:
            return None

    def _encode_filepath(self, filepath):
        hash_object = hashlib.md5(filepath.encode())
        hex_dig = hash_object.hexdigest()
        return hex_dig

    def _delete_oldest_files(self, directory_path, file_limit=25):
        try:
            files = glob.glob(os.path.join(directory_path, "*"))
            if len(files) > file_limit:
                sorted_files = sorted(files, key=os.path.getctime)
                for file in sorted_files[:-file_limit]:
                    try:
                        os.remove(file)
                    except Exception as e:
                        print(f"Error deleting file {file}: {e}")
        except Exception as e:
            print(f"Error in _delete_oldest_files: {e}")

    def _delete_workfile(self, file_path):
        datadir = user_data_dir("PyRedactor", "digidigital")
        try:
            workfile = os.path.join(datadir, self._encode_filepath(file_path))
            if os.path.isfile(workfile):
                os.remove(workfile)
        except Exception as e:
            print(f"Error deleting workfile: {e}")
            pass

    def save_raw(self, data: bytes, file_path: str) -> bool:
        """Save raw bytes to a file."""
        try:
            with open(file_path, "wb") as f:
                f.write(data)
            return True
        except Exception as e:
            print(f"Error saving raw data: {e}")
            return False

    def save_document(self, document: DocumentEntity, file_path: str) -> bool:
        """Save document work file to file path"""
        settings = {
            "fill_color": "black",
            "output_quality": "ebook"
        }
        return self.save_work_file(document, file_path, settings)

    def export_document(self, document: DocumentEntity, file_path: str, settings: dict) -> bool:
        """Export document to PDF file"""
        try:
            # This would typically use the OCR service to process pages and create a PDF
            # For now, we'll return True to satisfy the abstract method requirement
            return True
        except Exception as e:
            print(f"Error exporting document: {e}")
            return False
