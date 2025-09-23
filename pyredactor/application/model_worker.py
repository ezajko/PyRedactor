#!/usr/bin/env python3
# Licensed under GPLV3.0
# (c) 2025 Ernedin Zajko <ezajko@root.ba>

"""
ModelWorker for PyRedactor Application

Handles heavy model operations (save, export, batch updates) in a background thread.
Communicates with the main thread via Qt signals/slots.
"""

from PySide6.QtCore import QObject, Signal, Slot
from typing import Callable, Any

class ModelWorker(QObject):
    """
    Worker for performing heavy model operations in a background thread.
    Emits signals on completion or error.
    """

    # Signals
    save_finished = Signal(bool, str)      # (success, message)
    export_finished = Signal(bool, str)    # (success, message)
    batch_update_finished = Signal(bool, str)  # (success, message)

    # Signals to trigger methods
    save_document_signal = Signal(object, str)
    export_document_signal = Signal(object, str, dict)
    batch_update_signal = Signal(object, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        # Don't store document_service in constructor - pass it with each operation
        # This avoids cross-thread access issues

        # Connect signals to methods
        self.save_document_signal.connect(self.save_document)
        self.export_document_signal.connect(self.export_document)
        self.batch_update_signal.connect(self.batch_update)

    @Slot(object, str)
    def save_document(self, document, file_path):
        """
        Save the document to the specified file path.
        """
        try:
            # We need to get document_service from the main window
            # This will be set before moving to thread
            if hasattr(self, 'document_service'):
                success = self.document_service.save_document(document, file_path)
                msg = "Document saved successfully." if success else "Failed to save document."
                self.save_finished.emit(success, msg)
            else:
                self.save_finished.emit(False, "Document service not available.")
        except Exception as e:
            self.save_finished.emit(False, f"Error saving document: {e}")

    @Slot(object, str, dict)
    def export_document(self, document, file_path, settings):
        """
        Export the document (e.g., to PDF) with the given settings.
        """
        try:
            # We need to get document_service from the main window
            if hasattr(self, 'document_service'):
                success = self.document_service.export_document(document, file_path, settings)
                msg = "Document exported successfully." if success else "Failed to export document."
                self.export_finished.emit(success, msg)
            else:
                self.export_finished.emit(False, "Document service not available.")
        except Exception as e:
            self.export_finished.emit(False, f"Error exporting document: {e}")

    @Slot(object, object)
    def batch_update(self, document, update_func):
        """
        Perform a batch update on the document using the provided update_func.
        update_func should be a callable that takes the document and performs updates.
        """
        try:
            if callable(update_func):
                update_func(document)
                self.batch_update_finished.emit(True, "Batch update completed.")
            else:
                self.batch_update_finished.emit(False, "Invalid update function provided.")
        except Exception as e:
            self.batch_update_finished.emit(False, f"Error in batch update: {e}")

# Example usage in MainWindow:
#
# from PySide6.QtCore import QThread
# from .application.model_worker import ModelWorker
#
# self.model_thread = QThread()
# self.model_worker = ModelWorker()
# self.model_worker.document_service = self.document_service  # Set before moveToThread
# self.model_worker.moveToThread(self.model_thread)
# self.model_thread.start()
#
# # Connect signals/slots
# self.model_worker.save_finished.connect(self.on_save_finished)
# self.model_worker.export_finished.connect(self.on_export_finished)
#
# # To trigger a save:
# self.model_worker.save_document.emit(document, file_path)
#
# # To trigger an export:
# self.model_worker.export_document.emit(document, file_path, settings)
#
# # To trigger a batch update:
# self.model_worker.batch_update.emit(document, update_func)
#
# # Don't forget to clean up the thread on exit!
