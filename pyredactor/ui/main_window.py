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

class MainWindow(QMainWindow):
    def __init__(self, document_service: DocumentManagementService, redaction_service: RedactionService, settings_service: SettingsManagementService):
        try:
            super().__init__()

            print("[DEBUG] MainWindow: __init__ started")

            self.document_service = document_service
            self.redaction_service = redaction_service
            self.settings_service = settings_service

            self.setWindowTitle("PyRedactor")
            self.resize(1300, 900)

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

            # --- Undo stack for marker actions ---
            self.undo_stack = []
            self._undo_enabled = True

            available_langs = self.get_available_ocr_languages()
            if available_langs:
                self.ocr_lang = os.getenv('PYREDACTOR_OCR_LANG', available_langs[0])
                if self.ocr_lang not in available_langs:
                    self.ocr_lang = available_langs[0]
            else:
                self.ocr_lang = "eng"

            # Initial undo state will be pushed after a document is loaded

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

            # --- Undo shortcut ---
            undo_shortcut = QAction(self)
            undo_shortcut.setShortcut("Ctrl+Z")
            undo_shortcut.triggered.connect(self.undo)
            self.addAction(undo_shortcut)

            print("[DEBUG] MainWindow: __init__ finished")
        except Exception as e:
            import traceback
            print("[EXCEPTION] MainWindow __init__ failed:", e)
            traceback.print_exc()

    def push_undo_state(self):
        """
        Push a deep copy of the current page's rectangles to the undo stack.
        """
        try:
            print("[DEBUG] push_undo_state: called")
            document = self.document_service.get_current_document()
            if document:
                page = document.get_current_page()
                if page:
                    print(f"[DEBUG] push_undo_state: pushing {len(page.rectangles)} rectangles to undo_stack")
                    self.undo_stack.append(copy.deepcopy(page.rectangles))
                else:
                    print("[DEBUG] push_undo_state: no current page")
            else:
                print("[DEBUG] push_undo_state: no current document")
        except Exception as e:
            import traceback
            print("[EXCEPTION] push_undo_state failed:", e)
            traceback.print_exc()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete or event.key() == Qt.Key_D:
            selected_items = self.scene.selectedItems()
            for item in selected_items:
                if isinstance(item, ResizableRectItem):
                    self.push_undo_state()
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
                    self.push_undo_state()
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
                    self.push_undo_state()
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
                            self.redaction_service.move_redaction_rectangle(page, item._entity_id, delta_x, delta_y)
                            print(f"[DEBUG] MainWindow: Updated marker position in document data (ID: {item._entity_id})")
            self.scene.update() # Force repaint
        super().keyPressEvent(event)

    def _create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(32, 32))
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolbar.layout().setSpacing(10)
        self.addToolBar(toolbar)

        open_action = QAction(get_icon_from_theme("document-open", "open"), "Open", self)
        open_action.triggered.connect(self.open_file)

        save_action = QAction(get_icon_from_theme("document-save", "save"), "Save", self)
        save_action.triggered.connect(self.save_edited_document)

        save_as_action = QAction(get_icon_from_theme("document-save-as", "save_as"), "Save As", self)
        save_as_action.triggered.connect(self.save_as_edited_document)



        undo_action = QAction(get_icon_from_theme("edit-undo", "undo"), "Undo", self)
        undo_action.triggered.connect(self.undo)

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
        toolbar.addAction(undo_action)
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
            # Push undo state for marker creation
            self.push_undo_state()

            class LoaderWorker(QObject):
                finished = Signal(object)
                def __init__(self, document_service, file_path):
                    super().__init__()
                    self.document_service = document_service
                    self.file_path = file_path
                def run(self):
                    doc = self.document_service.load_document(self.file_path)
                    self.finished.emit(doc)

            progress = QProgressDialog(f"Loading file: {os.path.basename(file_path)}", None, 0, 0, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.setWindowTitle(f"Loading: {os.path.basename(file_path)}")
            progress.setMinimumDuration(0)
            progress.show()
            QApplication.processEvents()

            self._loader_thread = QThread()
            self._loader_worker = LoaderWorker(self.document_service, file_path)
            self._loader_worker.moveToThread(self._loader_thread)
            self._loader_thread.started.connect(self._loader_worker.run)
            self._loader_worker.finished.connect(self._loader_thread.quit)
            self._loader_worker.finished.connect(progress.close)
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
            self._loader_worker.finished.connect(on_loaded)
            self._loader_thread.start()
            progress.exec()

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
                    rect_item = ResizableRectItem(QRectF(
                        rect_entity.start_point[0],
                        rect_entity.start_point[1],
                        rect_entity.width,
                        rect_entity.height
                    ), entity_id=rect_entity.id)
                    rect_item.setBrush(QBrush(QColor(rect_entity.color))) # Use base color
                    rect_item.setOpacity(0.5) # 50% transparency
                    self.scene.addItem(rect_item)

            self.update_status_bar()
            self.page_list.setCurrentRow(page_num)
            # --- Clear undo stack on page change ---
            self.undo_stack.clear()

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

    def undo(self):
        document = self.document_service.get_current_document()
        if document:
            page = document.get_current_page()
            if page:
                self.push_undo_state()
                self.redaction_service.clear_all_redactions(page)
                self.show_page(document.current_page_index)

    def delete_all(self):
        document = self.document_service.get_current_document()
        if document:
            page = document.get_current_page()
            if page:
                self.push_undo_state()
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

        self._export_document(save_file_path)

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

            from PySide6.QtCore import QThread, Signal, QObject

            class ExportWorker(QObject):
                finished = Signal(bool)
                def __init__(self, document_service, document, save_file_path, settings):
                    super().__init__()
                    self.document_service = document_service
                    self.document = document
                    self.save_file_path = save_file_path
                    self.settings = settings
                def run(self):
                    result = self.document_service.export_document(self.document, self.save_file_path, self.settings)
                    self.finished.emit(result)

            progress = QProgressDialog(f"Exporting PDF: {os.path.basename(save_file_path)}", None, 0, 0, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.setWindowTitle(f"Exporting: {os.path.basename(save_file_path)}")
            progress.setMinimumDuration(0)
            progress.show()
            QApplication.processEvents()

            self._export_thread = QThread()
            self._export_worker = ExportWorker(self.document_service, document, save_file_path, settings)
            self._export_worker.moveToThread(self._export_thread)
            self._export_thread.started.connect(self._export_worker.run)
            self._export_worker.finished.connect(self._export_thread.quit)
            self._export_worker.finished.connect(progress.close)
            def on_exported(success):
                if success:
                    QMessageBox.information(self, "Export PDF", f"Document exported successfully to {save_file_path}")
                else:
                    QMessageBox.critical(self, "Export PDF", "Failed to export document.")
            self._export_worker.finished.connect(on_exported)
            self._export_thread.start()
            progress.exec()

    def about(self):
        QMessageBox.about(self, "About PyRedactor",
                          "PyRedactor PDF Redaction Software\n\n"
                          "Version 0.1.0\n"
                          "Licensed under GPL V3.0\n\n"
                          "©2025 Ernedin Zajko <ezajko@root.ba>")


        # Only undo if there is a previous state
        if len(self.undo_stack) > 1:
            self.undo_stack.pop()  # Remove current state
            prev_rectangles = copy.deepcopy(self.undo_stack[-1])
            page.rectangles = prev_rectangles
            self.show_page(document.current_page_index)
        elif len(self.undo_stack) == 1:
            # Undo to empty state
            self.undo_stack.pop()
            page.rectangles = []
            self.show_page(document.current_page_index)

# --- Patch for robust undo on marker move/resize via mouse ---
from PySide6.QtWidgets import QGraphicsRectItem
from PySide6.QtCore import Qt

# Patch ResizableRectItem to push undo state on mouse press for move/resize
from PyRedactor.pyredactor.ui.graphics_items import ResizableRectItem, HandleItem

def patched_mousePressEvent(self, event):
    # If left mouse button and not already selected, push undo state
    if event.button() == Qt.LeftButton:
        main_window = self.scene().views()[0].window()
        if main_window and hasattr(main_window, "push_undo_state"):
            main_window.push_undo_state()
    QGraphicsRectItem.mousePressEvent(self, event)

ResizableRectItem.mousePressEvent = patched_mousePressEvent

def patched_handle_mousePressEvent(self, event):
    if event.button() == Qt.LeftButton:
        main_window = self.scene().views()[0].window()
        if main_window and hasattr(main_window, "push_undo_state"):
            main_window.push_undo_state()
    QGraphicsRectItem.mousePressEvent(self, event)

HandleItem.mousePressEvent = patched_handle_mousePressEvent


if __name__ == "__main__":
    app = QApplication(sys.argv)
    sys.exit(app.exec())
