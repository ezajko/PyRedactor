#!/usr/bin/env python3
# Licensed under GPLV3.0
# (c) 2025 Ernedin Zajko <ezajko@root.ba>

"""
Document Loader Worker for PyRedactor Application

Handles document loading operations in a background thread with progress updates.
"""

from PySide6.QtCore import QObject, Signal, Slot
from PIL.ImageQt import ImageQt
from PySide6.QtGui import QPixmap

class DocumentLoaderWorker(QObject):
    """
    Worker for performing document loading operations in a background thread.
    Emits signals for progress updates and completion.
    """

    # Progress signals
    progress_update = Signal(str, int)  # (message, percentage)
    page_loaded = Signal(object, int)   # (thumbnail_pixmap, page_index)
    finished = Signal(object)           # (document)
    error = Signal(str)                 # (error_message)

    def __init__(self, document_service, file_path, parent=None):
        super().__init__(parent)
        self.document_service = document_service
        self.file_path = file_path
        self._cancelled = False

    @Slot()
    def load_document(self):
        """Load document with progress updates"""
        try:
            self.progress_update.emit("Loading document...", 0)

            # Load the document
            document = self.document_service.load_document(self.file_path)

            if not document:
                self.error.emit("Failed to load document")
                return

            if self._cancelled:
                self.finished.emit(None)
                return

            self.progress_update.emit("Processing pages...", 50)

            # Process each page for thumbnails
            total_pages = len(document.pages)
            for i, page in enumerate(document.pages):
                if self._cancelled:
                    self.finished.emit(None)
                    return

                # Update progress
                progress = int(50 + (i / total_pages) * 50)  # 50-100% for page processing
                self.progress_update.emit(f"Processing page {i+1} of {total_pages}...", progress)

                # Create thumbnail
                if page.image:
                    thumbnail = page.image.copy()
                    thumbnail.thumbnail((100, 100))
                    self.page_loaded.emit(thumbnail, i)

            self.progress_update.emit("Document loaded successfully!", 100)
            self.finished.emit(document)

        except Exception as e:
            self.error.emit(str(e))

    def cancel(self):
        """Cancel the load operation"""
        self._cancelled = True
