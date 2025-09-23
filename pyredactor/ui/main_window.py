#!/usr/bin/env python3
# Licensed under GPLV3.0
# (c) 2025 Ernedin Zajko <ezajko@root.ba>

"""
Main Window for PyRedactor Application
"""

import sys
import os
import json
import subprocess
from functools import partial
import pytesseract

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QToolBar, QGraphicsView, QGraphicsScene, QFileDialog,
    QRubberBand, QGraphicsRectItem, QMessageBox, QStatusBar, QDockWidget, QListWidget, QListWidgetItem,
    QComboBox, QCheckBox, QProgressDialog
)
from PySide6.QtGui import QAction, QIcon, QPixmap, QColor, QBrush, QPen
from PySide6.QtCore import Qt, QPoint, QRect, QSize, QRectF, QThread, Signal

from ..utils.icon_utils import get_icon_from_theme, create_colorful_icon
from PIL.ImageQt import ImageQt
import io
import copy

from .graphics_items import ResizableRectItem, PhotoViewer

from ..core.services.document_management import DocumentManagementService
from ..core.services.redaction import RedactionService
from ..core.services.settings import SettingsManagementService

from ..application.model_worker import ModelWorker
from PySide6.QtCore import QThread

class MainWindow(QMainWindow):
    def __init__(self, document_service: DocumentManagementService, redaction_service: RedactionService, settings_service: SettingsManagementService):
        super().__init__()

        print("[DEBUG] MainWindow: __init__ started")

        self.document_service = document_service
        self.redaction_service = redaction_service
        self.settings_service = settings_service

        self.setWindowTitle("PyRedactor")
        self.resize(1300, 900)

        # --- ModelWorker for background model operations ---
        # Temporarily disable threading to fix issues
        # self.model_thread = QThread()
        self.model_worker = ModelWorker()
        self.model_worker.document_service = self.document_service
        # self.model_worker.moveToThread(self.model_thread)
        # self.model_thread.start()
        # self.model_worker.save_finished.connect(self.on_save_finished)
        # self.model_worker.export_finished.connect(self.on_export_finished)
        # self.model_worker.batch_update_finished.connect(self.on_batch_update_finished)

        self.fill_color = 'black'
        self.output_quality = 'ebook'
        self.history_length = 30
        self.color_list = ["#000000", "#ffffff", "#ff0000", "#00ff00"] # Black, White, Red, Green (hex codes)

        self.page_list = QListWidget()
        self.scene = QGraphicsScene()
        self.view = PhotoViewer(self)
        self.view.setScene(self.scene)

        self.ocr_enabled = True

        print("[DEBUG] MainWindow: UI widgets created")

        # Temporarily disable OCR language detection to avoid hangs
        # available_langs = self.get_available_ocr_languages()
        available_langs = ["eng"]  # Default to English
        if available_langs:
            self.ocr_lang = os.getenv('PYREDACTOR_OCR_LANG', available_langs[0])
            if self.ocr_lang not in available_langs:
                self.ocr_lang = available_langs[0]
        else:
            self.ocr_lang = "eng"

        print("[DEBUG] MainWindow: Calling _create_toolbar()")
        self._create_toolbar()
        print("[DEBUG] MainWindow: Toolbar created")

        print("[DEBUG] MainWindow: Setting central widget")
        self.setCentralWidget(self.view)

        print("[DEBUG] MainWindow: Creating page browser")
        self._create_page_browser()

        print("[DEBUG] MainWindow: Setting status bar")
        self.setStatusBar(QStatusBar(self))

        print("[DEBUG] MainWindow: Updating status bar")
        self.update_status_bar()

        print("[DEBUG] MainWindow: __init__ finished")



    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete or event.key() == Qt.Key_D:
            selected_items = self.scene.selectedItems()
            for item in selected_items:
                if isinstance(item, ResizableRectItem):
                    # Remove from scene
                    self.scene.removeItem(item)
                    print(f"[DEBUG] MainWindow: Deleted marker from scene (ID: {item._entity_id})")

                    # Remove from document data
                    document = self.document_service.get_current_document()
                    if document:
                        page = document.get_current_page()
                        if page:
                            self.redaction_service.remove_redaction_rectangle(page, item._entity_id)
                            print(f"[DEBUG] MainWindow: Deleted marker from document data (ID: {item._entity_id})")
            self.scene.update() # Force repaint
        elif event.key() == Qt.Key_C:
            selected_items = self.scene.selectedItems()
            for item in selected_items:
                if isinstance(item, ResizableRectItem):
                    current_color_index = (self.color_list.index(item.brush().color().name()) + 1) % len(self.color_list)
                    new_color_name = self.color_list[current_color_index]
                    new_color = QColor(new_color_name)

                    item.setBrush(QBrush(new_color)) # Apply new color to scene item
                    print(f"[DEBUG] MainWindow: Changed marker color to {new_color_name} (ID: {item._entity_id})")

                    # Update document data
                    document = self.document_service.get_current_document()
                    if document:
                        page = document.get_current_page()
                        if page:
                            self.redaction_service.change_redaction_color(page, item._entity_id, new_color_name)
                            print(f"[DEBUG] MainWindow: Updated marker color in document data (ID: {item._entity_id})")
            self.scene.update() # Force repaint
        elif event.key() in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
            selected_items = self.scene.selectedItems()
            for item in selected_items:
                if isinstance(item, ResizableRectItem):
                    delta_x = 0
                    delta_y = 0
                    step = 1 # Move by 1 pixel

                    if event.key() == Qt.Key_Up:
                        delta_y = -step
                    elif event.key() == Qt.Key_Down:
                        delta_y = step
                    elif event.key() == Qt.Key_Left:
                        delta_x = -step
                    elif event.key() == Qt.Key_Right:
                        delta_x = step

                    # Move in UI
                    item.setPos(item.pos().x() + delta_x, item.pos().y() + delta_y)
                    print(f"[DEBUG] MainWindow: Moved marker (ID: {item._entity_id}) in UI by ({delta_x}, {delta_y})")

                    # Update document data
                    document = self.document_service.get_current_document()
                    if document:
                        page = document.get_current_page()
                        if page:
                            # Update the model to match the new position
                            rect = item.rect()
                            pos = item.pos()
                            start_point = (rect.topLeft().x() + pos.x(), rect.topLeft().y() + pos.y())
                            end_point = (rect.bottomRight().x() + pos.x(), rect.bottomRight().y() + pos.y())
                            rectangle_entity = page.get_rectangle(item._entity_id)
                            if rectangle_entity:
                                rectangle_entity.start_point = start_point
                                rectangle_entity.end_point = end_point
                            print(f"[DEBUG] MainWindow: Updated marker position in document data (ID: {item._entity_id})")
            self.scene.update() # Force repaint
        super().keyPressEvent(event)

    def _create_toolbar(self):
        print("[DEBUG] MainWindow: _create_toolbar started")
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(32, 32))
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolbar.layout().setSpacing(10)
        self.addToolBar(toolbar)
        print("[DEBUG] MainWindow: Toolbar created")

        open_action = QAction(get_icon_from_theme("document-open", "open"), "Open", self)
        open_action.triggered.connect(self.open_file)

        save_action = QAction(get_icon_from_theme("document-save", "save"), "Save", self)
        save_action.triggered.connect(self.save_edited_document)

        save_as_action = QAction(get_icon_from_theme("document-save-as", "save_as"), "Save As", self)
        save_as_action.triggered.connect(self.save_as_edited_document)

        delete_all_action = QAction(get_icon_from_theme("edit-delete", "delete"), "Delete All", self)
        delete_all_action.triggered.connect(self.delete_all)

        prev_page_action = QAction(get_icon_from_theme("go-previous", "prev_page"), "Previous", self)
        prev_page_action.triggered.connect(self.prev_page)

        next_page_action = QAction(get_icon_from_theme("go-next", "next_page"), "Next", self)
        next_page_action.triggered.connect(self.next_page)

        zoom_in_action = QAction(get_icon_from_theme("zoom-in", "zoom_in"), "Zoom In", self)
        zoom_in_action.triggered.connect(self.zoom_in)

        zoom_out_action = QAction(get_icon_from_theme("zoom-out", "zoom_out"), "Zoom Out", self)
        zoom_out_action.triggered.connect(self.zoom_out)

        quit_action = QAction(get_icon_from_theme("application-exit", "quit"), "Quit", self)
        quit_action.triggered.connect(self.close)

        about_action = QAction(get_icon_from_theme("help-about", "about"), "About", self)
        about_action.triggered.connect(self.about)

        toolbar.addAction(open_action)
        toolbar.addAction(save_action)
        toolbar.addAction(save_as_action)
        toolbar.addSeparator()
        toolbar.addAction(delete_all_action)
        toolbar.addSeparator()
        toolbar.addAction(prev_page_action)
        toolbar.addAction(next_page_action)
        toolbar.addSeparator()
        toolbar.addAction(zoom_in_action)
        toolbar.addAction(zoom_out_action)
        toolbar.addSeparator()

        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["screen", "ebook", "printer", "prepress"])
        self.quality_combo.setCurrentText(self.output_quality)
        self.quality_combo.currentTextChanged.connect(self.quality_changed)
        self.quality_combo.setMinimumHeight(32)
        toolbar.addWidget(self.quality_combo)
        toolbar.addSeparator()

        self.ocr_checkbox = QCheckBox("Enable OCR")
        self.ocr_checkbox.setChecked(self.ocr_enabled)
        self.ocr_checkbox.stateChanged.connect(self.ocr_enabled_changed)
        self.ocr_checkbox.setStyleSheet("QCheckBox { height: 32px; }")
        toolbar.addWidget(self.ocr_checkbox)

        self.ocr_lang_combo = QComboBox()
        available_langs = self.get_available_ocr_languages()
        if available_langs:
            self.ocr_lang_combo.addItems(available_langs)
            default_lang = self.ocr_lang if self.ocr_lang in available_langs else available_langs[0]
            self.ocr_lang_combo.setCurrentText(default_lang)
        else:
            self.ocr_lang_combo.addItems(["No languages found"])
            self.ocr_lang_combo.setEnabled(False)
            self.ocr_checkbox.setChecked(False)
            self.ocr_checkbox.setEnabled(False)
        self.ocr_lang_combo.currentTextChanged.connect(self.ocr_lang_changed)
        self.ocr_lang_combo.setMinimumHeight(32)
        toolbar.addWidget(self.ocr_lang_combo)
        toolbar.addSeparator()

        toolbar.addAction(quit_action)
        toolbar.addSeparator()
        toolbar.addAction(about_action)
        print("[DEBUG] MainWindow: _create_toolbar finished")

    def _create_page_browser(self):
        self.page_browser_dock = QDockWidget("Page Browser", self)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.page_browser_dock)
        self.page_browser_dock.setWidget(self.page_list)
        self.page_list.itemClicked.connect(self.on_page_selected)
        self.page_browser_dock.show()
        self.page_browser_dock.setFloating(False)
        self.page_browser_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)

    def get_available_ocr_languages(self):
        return self.document_service.ocr_service.get_available_languages()

    def ocr_lang_changed(self, lang):
        self.ocr_lang = lang

    def ocr_enabled_changed(self, state):
        self.ocr_enabled = state == Qt.Checked

    def quality_changed(self, quality):
        self.output_quality = quality



    def open_file(self, file_path: str = None):
        if not file_path:
            documents_path = os.path.expanduser("~/Documents")
            if not os.path.exists(documents_path):
                documents_path = os.path.expanduser("~")

            file_path, _ = QFileDialog.getOpenFileName(
                self, "Open File", documents_path, "PDF Files (*.pdf);;Image Files (*.png *.jpg *.bmp)"
            )

        if file_path:
            from PySide6.QtCore import QThread, Signal, QObject

            class LoaderWorker(QObject):
                finished = Signal(object)
                def __init__(self, document_service, file_path):
                    super().__init__()
                    self.document_service = document_service
                    self.file_path = file_path
                def run(self):
                    doc = self.document_service.load_document(self.file_path)
                    self.finished.emit(doc)

            # Temporarily disable threading for document loading
            # self._loader_thread = QThread()
            self._loader_worker = LoaderWorker(self.document_service, file_path)
            # self._loader_worker.moveToThread(self._loader_thread)
            # self._loader_thread.started.connect(self._loader_worker.run)
            # self._loader_worker.finished.connect(self._loader_thread.quit)
            # self._loader_worker.finished.connect(progress.close)

            # Run the loader directly
            document = self.document_service.load_document(file_path)

            def on_loaded(document):
                if document:
                    self.page_list.clear()
                    for i, page in enumerate(document.pages):
                        thumbnail = page.image.copy()
                        thumbnail.thumbnail((100, 100))
                        qimage = ImageQt(thumbnail)
                        pixmap = QPixmap.fromImage(qimage)
                        item = QListWidgetItem(QIcon(pixmap), f"Page {i+1}")
                        self.page_list.addItem(item)
                    self.show_page(0)
                    self.update_status_bar()
                    # Show loaded file info in status bar
                    self.statusBar().showMessage(
                        f"Loaded: {os.path.basename(file_path)} | {file_path} | Pages: {len(document.pages)} | Markers: {document.total_rectangles}"
                    )
                else:
                    QMessageBox.critical(self, "Error", f"Failed to open file: {file_path}")
            # self._loader_worker.finished.connect(on_loaded)
            on_loaded(document)
            # self._loader_thread.start()
            # progress.exec()

    def show_page(self, page_num: int):
        document = self.document_service.get_current_document()
        if document and 0 <= page_num < document.page_count:
            self.document_service.navigate_to_page(document, page_num)
            self.scene.clear()
            page = document.get_current_page()
            if page and page.image:
                self.scene.clear()
                qimage = ImageQt(page.image)
                pixmap = QPixmap.fromImage(qimage)
                self.scene.addPixmap(pixmap)
                self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

                for rect_entity in page.rectangles:
                    # Calculate width and height from start/end points
                    x0, y0 = rect_entity.start_point
                    x1, y1 = rect_entity.end_point
                    width = x1 - x0
                    height = y1 - y0
                    rect_item = ResizableRectItem(QRectF(0, 0, width, height), entity_id=rect_entity.id)
                    rect_item.setPos(x0, y0)
                    rect_item.setBrush(QBrush(QColor(rect_entity.color))) # Use base color
                    rect_item.setOpacity(0.5) # 50% transparency
                    self.scene.addItem(rect_item)

            self.update_status_bar()
            self.page_list.setCurrentRow(page_num)

    def next_page(self):
        document = self.document_service.get_current_document()
        if document:
            if self.document_service.navigate_next_page(document):
                self.show_page(document.current_page_index)

    def prev_page(self):
        document = self.document_service.get_current_document()
        if document:
            if self.document_service.navigate_previous_page(document):
                self.show_page(document.current_page_index)

    def on_page_selected(self, item):
        row = self.page_list.row(item)
        self.show_page(row)

    def update_status_bar(self):
        document = self.document_service.get_current_document()
        if document:
            file_info = f"{os.path.basename(document.file_path)} | {document.file_path}" if document.file_path else "Untitled"
            page_info = f"Page {document.current_page_index + 1} of {document.page_count}"
            marker_info = f"Markers: {document.total_rectangles}"
            self.statusBar().showMessage(f"{file_info} | {page_info} | {marker_info}")
        else:
            self.statusBar().showMessage("No file loaded")

    def zoom_in(self):
        self.view.scale(1.2, 1.2)

    def zoom_out(self):
        self.view.scale(0.8, 0.8)



    def delete_all(self):
        """
        Remove all markers from the current page and update the model.
        """
        document = self.document_service.get_current_document()
        if document:
            page = document.get_current_page()
            if page:
                self.redaction_service.clear_all_redactions(page)
                self.show_page(document.current_page_index)



    def save_edited_document(self):
        document = self.document_service.get_current_document()
        if not document:
            QMessageBox.warning(self, "Save Document", "No document to save.")
            return

        if not document.file_path:
            self.save_as_edited_document()
            return

        base_name = os.path.splitext(os.path.basename(document.file_path))[0]
        dir_name = os.path.dirname(document.file_path)
        redacted_filename = f"{base_name}.Redacted.pdf"
        save_file_path = os.path.join(dir_name, redacted_filename)

        # Call export directly without threading
        settings = {
            "ocr_enabled": self.ocr_enabled,
            "ocr_lang": self.ocr_lang,
            "output_quality": self.output_quality
        }
        self.model_worker.export_document(document, save_file_path, settings)

    def save_as_edited_document(self):
        document = self.document_service.get_current_document()
        if not document:
            QMessageBox.warning(self, "Save Document As", "No document to save.")
            return

        suggested_filename = "redacted_document.pdf"
        if document.file_path:
            base_name = os.path.splitext(os.path.basename(document.file_path))[0]
            suggested_filename = f"{base_name}.Redacted.pdf"

        save_file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Document As", suggested_filename, "PDF Files (*.pdf)"
        )
        if save_file_path:
            self._export_document(save_file_path)

    def _export_document(self, save_file_path):
        document = self.document_service.get_current_document()
        if document:
            settings = {
                "ocr_enabled": self.ocr_enabled,
                "ocr_lang": self.ocr_lang,
                "output_quality": self.output_quality
            }

            # Call export directly without threading
            self.model_worker.export_document(document, save_file_path, settings)

    def about(self):
        QMessageBox.about(self, "About PyRedactor",
                          "PyRedactor PDF Redaction Software\n\n"
                          "Version 0.1.0\n"
                          "Licensed under GPL V3.0\n\n"
                          "©2025 Ernedin Zajko <ezajko@root.ba>")

    def trigger_batch_marker_operation(self, update_func):
        """
        Trigger a batch marker/model operation in the background using ModelWorker.
        update_func should be a callable that takes the document and performs updates.
        """
        document = self.document_service.get_current_document()
        if document:
            self.model_worker.batch_update(document, update_func)
        else:
            QMessageBox.warning(self, "Batch Operation", "No document loaded.")

    def on_batch_update_finished(self, success, message):
        if success:
            QMessageBox.information(self, "Batch Operation", message)
            # Optionally refresh the UI
            self.show_page(self.document_service.get_current_document().current_page_index)
        else:
            QMessageBox.critical(self, "Batch Operation", message)

    def on_save_finished(self, success, message):
        if success:
            QMessageBox.information(self, "Save Document", message)
        else:
            QMessageBox.critical(self, "Save Document", message)

    def on_export_finished(self, success, message):
        if success:
            QMessageBox.information(self, "Export PDF", message)
        else:
            QMessageBox.critical(self, "Export PDF", message)

    def closeEvent(self, event):
        """Clean up threads when closing the application"""
        # Quit and wait for the model thread to finish (if threading is enabled)
        if hasattr(self, 'model_thread') and self.model_thread and hasattr(self.model_thread, 'isRunning') and self.model_thread.isRunning():
            self.model_thread.quit()
            self.model_thread.wait()
        # Clean up loader thread if it exists
        if hasattr(self, '_loader_thread') and self._loader_thread and hasattr(self._loader_thread, 'isRunning') and self._loader_thread.isRunning():
            self._loader_thread.quit()
            self._loader_thread.wait()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    sys.exit(app.exec())

    def closeEvent(self, event):
        """Clean up threads when closing the application"""
        # Quit and wait for the model thread to finish
        if hasattr(self, 'model_thread') and self.model_thread.isRunning():
            self.model_thread.quit()
            self.model_thread.wait()
        event.accept()
