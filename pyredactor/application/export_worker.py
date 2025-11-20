#!/usr/bin/env python3
# Licensed under GPLV3.0
# (c) 2025 Ernedin Zajko <ezajko@root.ba>

"""
Export Worker for PyRedactor Application

Handles PDF export operations in a background thread with progress updates.
"""

from PySide6.QtCore import QObject, Signal, Slot
from PyPDF2 import PdfMerger
import io

class ExportWorker(QObject):
    """
    Worker for performing PDF export operations in a background thread.
    Emits signals for progress updates and completion.
    """

    # Progress signals
    progress_update = Signal(str, int)  # (message, percentage)
    finished = Signal(bool, str, str)   # (success, message, file_path)
    error = Signal(str)                 # (error_message)

    def __init__(self, document_service, document, file_path, settings, parent=None):
        super().__init__(parent)
        self.document_service = document_service
        self.document = document
        self.file_path = file_path
        self.settings = settings
        self._cancelled = False

    @Slot()
    def export_document(self):
        """Export document with progress updates"""
        try:
            # Phase 1: Creating PDF
            self.progress_update.emit("Initializing PDF export process...", 0)

            merger = PdfMerger()
            total_pages = len(self.document.pages)

            self.progress_update.emit("Starting PDF creation with redactions...", 5)

            for i, page in enumerate(self.document.pages):
                if self._cancelled:
                    self.finished.emit(False, "Export cancelled by user", "")
                    return

                # Update progress with more detailed information
                creation_progress = int(5 + (i / total_pages) * 40)  # 5-45% for PDF creation
                self.progress_update.emit(f"Processing page {i+1} of {total_pages} - applying redactions...", creation_progress)

                # Process page with OCR
                ocr_enabled = self.settings.get("ocr_enabled", True)
                ocr_lang = self.settings.get("ocr_lang", "eng")
                quality = self.settings.get("output_quality", "ebook")

                if ocr_enabled:
                    self.progress_update.emit(f"Processing page {i+1} of {total_pages} - running OCR ({ocr_lang})...", creation_progress + 2)
                else:
                    self.progress_update.emit(f"Processing page {i+1} of {total_pages} - preparing page...", creation_progress + 2)

                pdf_page = self.document_service.ocr_service.process_page(page, ocr_lang, ocr_enabled, quality)

                if pdf_page:
                    merger.append(io.BytesIO(pdf_page))
                else:
                    self.error.emit(f"Failed to process page {i+1} - skipping...")

            # Phase 2: Finalizing PDF
            self.progress_update.emit("Finalizing PDF structure...", 75)

            output_stream = io.BytesIO()
            merger.write(output_stream)
            merger.close()

            # Phase 3: Saving file
            self.progress_update.emit("Writing PDF to disk...", 90)

            success = self.document_service.document_repository.save_raw(
                output_stream.getvalue(),
                self.file_path
            )

            if success:
                self.progress_update.emit("Export completed successfully!", 100)
                self.finished.emit(True, f"Document exported successfully to:\n{self.file_path}", self.file_path)
            else:
                self.finished.emit(False, "Failed to save document to disk - check disk space and permissions", "")

        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit(False, f"Error during export: {str(e)}", "")

    def cancel(self):
        """Cancel the export operation"""
        self._cancelled = True
