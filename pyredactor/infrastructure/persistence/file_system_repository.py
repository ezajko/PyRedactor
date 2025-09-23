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

class FileSystemDocumentRepository(DocumentRepositoryInterface):
    """File system implementation of the document repository"""

    def load_document(self, file_path: str) -> Optional[DocumentEntity]:
        """Load a document from file path"""
        try:
            document = DocumentEntity(file_path=file_path)

            if file_path.lower().endswith('.pdf'):
                pdf = pdfium.PdfDocument(file_path)
                for i in range(len(pdf)):
                    pil_image = pdf[i].render(scale=2).to_pil()
                    page = PageEntity(
                        page_number=i,
                        image=pil_image,
                        size=pdf[i].get_size()
                    )
                    document.add_page(page)
            else:
                pil_image = Image.open(file_path)
                page = PageEntity(
                    page_number=0,
                    image=pil_image,
                    size=pil_image.size
                )
                document.add_page(page)

            return document
        except Exception as e:
            print(f"Error loading document: {e}")
            return None

    def save_document(self, document: DocumentEntity, file_path: str) -> bool:
        """Save document work file to file path"""
        settings = {
            "fill_color": "black",
            "output_quality": "ebook"
        }
        return self.save_work_file(document, file_path, settings)

    def export_document(self, document: DocumentEntity, file_path: str, settings: dict) -> bool:
        pass

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
