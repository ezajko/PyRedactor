#!/usr/bin/env python3
# Licensed under GPLV3.0
# (c) 2025 Ernedin Zajko <ezajko@root.ba>

"""
Batch Operation Worker for PyRedactor Application

Handles batch operations in a background thread with progress updates.
"""

from PySide6.QtCore import QObject, Signal, Slot

class BatchOperationWorker(QObject):
    """
    Worker for performing batch operations in a background thread.
    Emits signals for progress updates and completion.
    """
    
    # Progress signals
    progress_update = Signal(str, int)  # (message, percentage)
    finished = Signal(bool, str)        # (success, message)
    error = Signal(str)                 # (error_message)
    
    def __init__(self, document, update_func, operation_name="Batch Operation", parent=None):
        super().__init__(parent)
        self.document = document
        self.update_func = update_func
        self.operation_name = operation_name
        self._cancelled = False
    
    @Slot()
    def execute_batch_operation(self):
        """Execute batch operation with progress updates"""
        try:
            self.progress_update.emit(f"Starting {self.operation_name}...", 0)
            
            # Execute the batch operation
            if callable(self.update_func):
                self.update_func(self.document)
                self.progress_update.emit(f"{self.operation_name} completed successfully!", 100)
                self.finished.emit(True, f"{self.operation_name} completed successfully!")
            else:
                error_msg = "Invalid update function provided"
                self.error.emit(error_msg)
                self.finished.emit(False, error_msg)
                
        except Exception as e:
            error_msg = f"Error during {self.operation_name}: {str(e)}"
            self.error.emit(error_msg)
            self.finished.emit(False, error_msg)
    
    def cancel(self):
        """Cancel the batch operation"""
        self._cancelled = True

