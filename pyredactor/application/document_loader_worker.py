#!/usr/bin/env python3
# Licensed under GPLV3.0
# (c) 2025 Ernedin Zajko <ezajko@root.ba>

"""
Document Loader Worker for PyRedactor Application

Handles document loading operations in a background thread with progress updates.
"""

from PySide6.QtCore import QObject, Signal, Slot, QThread
from PIL.ImageQt import ImageQt
from PySide6.QtGui import QImage

class DocumentLoaderWorker(QObject):
    """
    Worker for performing document loading operations in a background thread.
    Emits signals for progress updates and completion.
    """

    # Progress signals
    progress_update = Signal(str, int)  # (message, percentage)
    page_loaded = Signal(object, int)   # (thumbnail_qimage, page_index)
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
            self.progress_update.emit("Initializing document loader...", 0)

            # Check if unpaper preprocessing is available
            unpaper_available = False
            try:
                from ..ocr.unpaper_preprocessing import UnpaperPreprocessingService
                unpaper_service = UnpaperPreprocessingService()
                unpaper_available = unpaper_service.is_available()
            except ImportError:
                pass

            # Load the document
            if unpaper_available:
                self.progress_update.emit("Loading document from file (unpaper preprocessing available)...", 5)
            else:
                self.progress_update.emit("Loading document from file...", 5)

            # Define callback for repository
            def repo_progress_callback(current, total, message):
                if self._cancelled:
                    raise InterruptedError("Loading cancelled")
                
                # Map 0-100% of repository loading to 5-80% of overall progress
                percentage = 5 + int((current / total) * 75)
                self.progress_update.emit(message, percentage)

            try:
                document = self.document_service.load_document(self.file_path, repo_progress_callback)
            except InterruptedError:
                self.finished.emit(None)
                return

            if not document:
                self.error.emit("Failed to load document - invalid file format or corrupted file")
                return

            if self._cancelled:
                self.finished.emit(None)
                return

            self.progress_update.emit(f"Document loaded - processing thumbnails...", 80)

            # Process each page for thumbnails
            total_pages = len(document.pages)
            for i, page in enumerate(document.pages):
                if self._cancelled:
                    self.finished.emit(None)
                    return

                # Update progress for thumbnails (80-95%)
                page_progress = 80 + int((i / total_pages) * 15)
                self.progress_update.emit(f"Generating thumbnail for page {i+1}...", page_progress)

                # Create thumbnail
                if page.image:
                    thumbnail = page.image.copy()
                    thumbnail.thumbnail((100, 100))
                    
                    # Convert to QImage in worker thread to save main thread time
                    # ImageQt returns a QImage wrapper around PIL image
                    # We copy it to detach from PIL image and ensure it's a pure Qt object
                    q_image = ImageQt(thumbnail).copy()
                    
                    self.page_loaded.emit(q_image, i)
                
                # Small sleep to prevent flooding the event loop and allow UI updates
                QThread.msleep(10)

            self.progress_update.emit("Document processing completed successfully!", 100)
            self.finished.emit(document)

        except Exception as e:
            self.error.emit(f"Error loading document: {str(e)}")

    def cancel(self):
        """Cancel the load operation"""
        self._cancelled = True
