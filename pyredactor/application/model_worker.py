#!/usr/bin/env python3
# Licensed under GPLV3.0
# (c) 2025 Ernedin Zajko <ezajko@root.ba>

"""
ModelWorker for PyRedactor Application

Handles heavy model operations (save, export, batch updates) in a background thread.
Communicates with the main thread via Qt signals/slots.
"""

from PySide6.QtCore import QObject, Signal, Slot

class ModelWorker(QObject):
    """
    Worker for performing heavy model operations in a background thread.
    Emits signals on completion or error.
    """

    # Signals
    save_finished = Signal(bool, str)      # (success, message)
    export_finished = Signal(bool, str)    # (success, message)
    batch_update_finished = Signal(bool, str)  # (success, message)

    def __init__(self, document_service, parent=None):
        super().__init__(parent)
        self.document_service = document_service

    @Slot(object, str)
    def save_document(self, document, file_path):
        """
        Save the document to the specified file path.
        """
        try:
            success = self.document_service.save_document(document, file_path)
            msg = "Document saved successfully." if success else "Failed to save document."
            self.save_finished.emit(success, msg)
        except Exception as e:
            self.save_finished.emit(False, f"Error saving document: {e}")

    @Slot(object, str, dict)
    def export_document(self, document, file_path, settings):
        """
        Export the document (e.g., to PDF) with the given settings.
        """
        try:
            success = self.document_service.export_document(document, file_path, settings)
            msg = "Document exported successfully." if success else "Failed to export document."
            self.export_finished.emit(success, msg)
        except Exception as e:
            self.export_finished.emit(False, f"Error exporting document: {e}")

    @Slot(object, object)
    def batch_update(self, document, update_func):
        """
        Perform a batch update on the document using the provided update_func.
        update_func should be a callable that takes the document and performs updates.
        """
        try:
            update_func(document)
            self.batch_update_finished.emit(True, "Batch update completed.")
        except Exception as e:
            self.batch_update_finished.emit(False, f"Error in batch update: {e}")

# Example usage in MainWindow:
#
# from PySide6.QtCore import QThread
# from .application.model_worker import ModelWorker
#
# self.model_thread = QThread()
# self.model_worker = ModelWorker(self.document_service)
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
