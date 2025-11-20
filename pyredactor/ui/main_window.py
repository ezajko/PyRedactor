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
    QComboBox, QCheckBox, QProgressDialog, QDialog, QPushButton, QSlider, QVBoxLayout, QHBoxLayout, QSpinBox,
    QWidget, QSizePolicy
)
from PySide6.QtGui import QAction, QIcon, QPixmap, QColor, QBrush, QPen
from PySide6.QtCore import Qt, QPoint, QRect, QSize, QRectF, QThread, Signal

from ..utils.icon_utils import get_icon_from_theme, create_colorful_icon
from PIL.ImageQt import ImageQt
import io
import copy

from .graphics_items import ResizableRectItem, PhotoViewer, CropRectItem

from ..core.services.document_management import DocumentManagementService
from ..core.services.redaction import RedactionService
from ..core.services.settings import SettingsManagementService

from ..application.model_worker import ModelWorker
from ..application.export_worker import ExportWorker
from ..application.document_loader_worker import DocumentLoaderWorker
from ..application.batch_worker import BatchOperationWorker
from PySide6.QtCore import QThread

class OCRLanguageLoader(QThread):
    """Worker thread to load OCR languages asynchronously"""
    languages_loaded = Signal(list)
    
    def run(self):
        try:
            langs = pytesseract.get_languages()
            self.languages_loaded.emit(langs)
        except Exception as e:
            print(f"Error loading OCR languages: {e}")
            self.languages_loaded.emit([])

class RotationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fine Rotation")
        self.resize(300, 100)
        self.angle = 0.0
        
        layout = QVBoxLayout(self)
        
        # Controls
        controls_layout = QHBoxLayout()
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(-100, 100) # -10.0 to 10.0 degrees
        self.slider.setValue(0)
        
        self.spinbox = QSpinBox()
        self.spinbox.setRange(-10, 10)
        self.spinbox.setSuffix("°")
        
        controls_layout.addWidget(QLabel("Angle:"))
        controls_layout.addWidget(self.slider)
        controls_layout.addWidget(self.spinbox)
        layout.addLayout(controls_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.apply_btn)
        layout.addLayout(btn_layout)
        
        # Connect signals
        self.slider.valueChanged.connect(self._on_slider_change)
        self.spinbox.valueChanged.connect(self._on_spinbox_change)
        
    def _on_slider_change(self, value):
        self.angle = value / 10.0
        self.spinbox.blockSignals(True)
        self.spinbox.setValue(int(self.angle))
        self.spinbox.blockSignals(False)
        
    def _on_spinbox_change(self, value):
        self.angle = float(value)
        self.slider.blockSignals(True)
        self.slider.setValue(int(self.angle * 10))
        self.slider.blockSignals(False)
        
    def get_angle(self):
        return self.angle

class CropDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crop Page")
        self.setWindowFlags(Qt.Tool) # Floating tool window
        self.resize(250, 150)
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Select Aspect Ratio:"))
        
        self.ratio_combo = QComboBox()
        self.ratio_combo.addItems(["Free", "A4 (Portrait)", "A4 (Landscape)", "Letter (Portrait)", "Letter (Landscape)"])
        self.ratio_combo.currentTextChanged.connect(self.parent().update_crop_ratio)
        layout.addWidget(self.ratio_combo)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        self.apply_btn = QPushButton("Apply Crop")
        self.apply_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.apply_btn)
        layout.addLayout(btn_layout)

class MainWindow(QMainWindow):
    def __init__(self, document_service: DocumentManagementService, redaction_service: RedactionService, settings_service: SettingsManagementService):
        super().__init__()

        self.document_service = document_service
        self.redaction_service = redaction_service
        self.settings_service = settings_service

        self.setWindowTitle("PyRedactor")
        self.resize(1300, 900)
        
        # Load settings
        self.settings = self.settings_service.load_settings()

        # Apply settings
        self.fill_color = self.settings.fill_color
        self.output_quality = self.settings.output_quality
        self.ocr_enabled = self.settings.ocr_enabled
        self.selected_ocr_langs = [self.settings.ocr_language] if self.settings.ocr_language else ["eng"]

        # --- ModelWorker for background model operations ---
        self.model_worker = ModelWorker()
        self.model_worker.document_service = self.document_service

        self.history_length = self.settings.history_length
        self.color_map = {
            "Black": "#000000", 
            "White": "#ffffff", 
            "Red": "#ff0000", 
            "Green": "#00ff00"
        }

        self.page_list = QListWidget()
        self.page_list.itemClicked.connect(self.on_page_selected)
        
        # Setup Dock Widget for Pages
        self.dock = QDockWidget("Pages", self)
        self.dock.setWidget(self.page_list)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock)

        self.scene = QGraphicsScene()
        self.view = PhotoViewer(self)
        self.view.setScene(self.scene)
        self.setCentralWidget(self.view)

        # OCR Settings
        self.available_ocr_langs = []
        
        # Start loading languages in background
        self.lang_loader = OCRLanguageLoader()
        self.lang_loader.languages_loaded.connect(self.on_languages_loaded)
        self.lang_loader.start()

        # Image enhancement options
        self.enhancement_enabled = False
        self.enhancement_brightness = 1.0
        self.enhancement_contrast = 1.0
        self.enhancement_sharpness = 1.0
        self.enhancement_auto_level = True
        self.enhancement_deskew = True
        self.enhancement_denoise = True
        
        # Crop state
        self.crop_mode = False
        self.crop_rect_item = None
        self.crop_dialog = None

        self.setup_toolbar()
        self.update_status_bar()

    def closeEvent(self, event):
        # Save settings on exit
        self.settings.fill_color = self.fill_color
        self.settings.output_quality = self.output_quality
        self.settings.ocr_enabled = self.ocr_enabled
        if self.selected_ocr_langs:
            self.settings.ocr_language = self.selected_ocr_langs[0]
            
        self.settings_service.save_settings(self.settings)
        super().closeEvent(event)

    def on_languages_loaded(self, langs):
        """Callback when OCR languages are loaded"""
        self.available_ocr_langs = langs
        # Ensure 'eng' is selected if available, otherwise first available
        if not self.selected_ocr_langs and langs:
            if 'eng' in langs:
                self.selected_ocr_langs = ['eng']
            else:
                self.selected_ocr_langs = [langs[0]]
        
        # Update UI if needed (e.g. enable language button)
        if hasattr(self, 'ocr_lang_btn'):
            self.ocr_lang_btn.setEnabled(True)
            self.update_ocr_lang_tooltip()

    def setup_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        # Open Action
        open_action = QAction(QIcon.fromTheme("document-open"), "Open", self)
        open_action.setStatusTip("Open a PDF document")
        open_action.triggered.connect(self.open_document)
        toolbar.addAction(open_action)

        # Save Action
        save_action = QAction(QIcon.fromTheme("document-save"), "Save", self)
        save_action.setStatusTip("Save redactions")
        save_action.triggered.connect(self.save_edited_document)
        toolbar.addAction(save_action)
        
        # Save As Action
        save_as_action = QAction(QIcon.fromTheme("document-save-as"), "Save As", self)
        save_as_action.setStatusTip("Save redactions as new file")
        save_as_action.triggered.connect(self.save_as_edited_document)
        toolbar.addAction(save_as_action)

        toolbar.addSeparator()
        
        # Undo Action
        undo_action = QAction(QIcon.fromTheme("edit-undo"), "Undo", self)
        undo_action.setStatusTip("Undo last action")
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.undo)
        toolbar.addAction(undo_action)
        
        # Reset Document Action
        reset_action = QAction(QIcon.fromTheme("view-refresh"), "Reset", self)
        reset_action.setStatusTip("Reset document to original state")
        reset_action.triggered.connect(self.reset_document)
        toolbar.addAction(reset_action)

        toolbar.addSeparator()

        # Zoom In
        zoom_in_action = QAction(QIcon.fromTheme("zoom-in"), "Zoom In", self)
        zoom_in_action.setStatusTip("Zoom In")
        zoom_in_action.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in_action)

        # Zoom Out
        zoom_out_action = QAction(QIcon.fromTheme("zoom-out"), "Zoom Out", self)
        zoom_out_action.setStatusTip("Zoom Out")
        zoom_out_action.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out_action)
        
        toolbar.addSeparator()
        
        # Previous Page
        prev_action = QAction(QIcon.fromTheme("go-previous"), "Prev Page", self)
        prev_action.setStatusTip("Go to previous page")
        prev_action.triggered.connect(self.prev_page)
        toolbar.addAction(prev_action)
        
        # Next Page
        next_action = QAction(QIcon.fromTheme("go-next"), "Next Page", self)
        next_action.setStatusTip("Go to next page")
        next_action.triggered.connect(self.next_page)
        toolbar.addAction(next_action)

        toolbar.addSeparator()

        # Delete Selected Marker
        delete_selected_action = QAction(QIcon.fromTheme("edit-clear"), "Delete Marker", self)
        delete_selected_action.setStatusTip("Delete selected marker")
        delete_selected_action.setShortcut("Delete")
        delete_selected_action.triggered.connect(self.delete_selected_marker)
        toolbar.addAction(delete_selected_action)

        # Delete All Markers
        delete_all_action = QAction(QIcon.fromTheme("edit-delete"), "Clear Page", self)
        delete_all_action.setStatusTip("Clear all markers on current page")
        delete_all_action.triggered.connect(self.delete_all)
        toolbar.addAction(delete_all_action)

        toolbar.addSeparator()

        # Color Selection
        color_label = QLabel("Color: ")
        toolbar.addWidget(color_label)
        
        self.color_combo = QComboBox()
        self.color_combo.addItems(list(self.color_map.keys()))
        # Set current color based on settings
        for name, hex_val in self.color_map.items():
            if hex_val.lower() == self.fill_color.lower():
                self.color_combo.setCurrentText(name)
                break
        self.color_combo.currentTextChanged.connect(self.change_marker_color)
        toolbar.addWidget(self.color_combo)

        toolbar.addSeparator()
        
        # Quality Selection
        quality_label = QLabel("Quality: ")
        toolbar.addWidget(quality_label)
        
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["Screen", "Ebook", "Printer", "Prepress"])
        self.quality_combo.setCurrentText(self.output_quality.capitalize())
        self.quality_combo.currentTextChanged.connect(self.change_quality)
        toolbar.addWidget(self.quality_combo)
        
        toolbar.addSeparator()

        # OCR Toggle
        self.ocr_checkbox = QCheckBox("OCR")
        self.ocr_checkbox.setToolTip("Enable OCR (Text Recognition) when saving")
        self.ocr_checkbox.setChecked(self.ocr_enabled)
        self.ocr_checkbox.toggled.connect(self.toggle_ocr)
        toolbar.addWidget(self.ocr_checkbox)
        
        # OCR Language Button
        self.ocr_lang_btn = QPushButton("Langs")
        self.ocr_lang_btn.setToolTip("Select OCR Languages")
        self.ocr_lang_btn.clicked.connect(self.open_ocr_language_dialog)
        self.ocr_lang_btn.setEnabled(False) # Disabled until languages load
        toolbar.addWidget(self.ocr_lang_btn)

        toolbar.addSeparator()

        # Rotate Left
        rotate_left_action = QAction(QIcon.fromTheme("object-rotate-left"), "Rot L", self)
        rotate_left_action.setStatusTip("Rotate page 90° Counter-Clockwise")
        rotate_left_action.triggered.connect(self.rotate_left)
        toolbar.addAction(rotate_left_action)

        # Rotate Right
        rotate_right_action = QAction(QIcon.fromTheme("object-rotate-right"), "Rot R", self)
        rotate_right_action.setStatusTip("Rotate page 90° Clockwise")
        rotate_right_action.triggered.connect(self.rotate_right)
        toolbar.addAction(rotate_right_action)
        
        # Fine Rotate
        fine_rotate_action = QAction(QIcon.fromTheme("transform-rotate"), "Fine Rot", self)
        fine_rotate_action.setStatusTip("Fine rotation for deskewing")
        fine_rotate_action.triggered.connect(self.fine_rotate)
        toolbar.addAction(fine_rotate_action)
        
        toolbar.addSeparator()
        
        # Crop Tool
        crop_action = QAction(QIcon.fromTheme("transform-crop"), "Crop", self)
        crop_action.setStatusTip("Crop page")
        crop_action.triggered.connect(self.toggle_crop_tool)
        toolbar.addAction(crop_action)
        
        toolbar.addSeparator()
        
        # About Action
        about_action = QAction(QIcon.fromTheme("help-about"), "About", self)
        about_action.setStatusTip("About PyRedactor")
        about_action.triggered.connect(self.about)
        toolbar.addAction(about_action)

    def rotate_left(self):
        """Rotate current page 90 degrees counter-clockwise"""
        self._rotate_page(90)

    def rotate_right(self):
        """Rotate current page 90 degrees clockwise"""
        self._rotate_page(-90)
        
    def fine_rotate(self):
        """Open dialog for fine rotation"""
        dialog = RotationDialog(self)
        if dialog.exec() == QDialog.Accepted:
            angle = dialog.get_angle()
            if angle != 0:
                self._rotate_page(angle)

    def _rotate_page(self, angle):
        """Helper to rotate page and refresh view"""
        # Cancel crop mode if active to prevent stale state
        if self.crop_mode:
            self.toggle_crop_tool()

        document = self.document_service.get_current_document()
        if not document:
            return

        # Warn user about clearing markers
        if document.total_rectangles > 0:
            reply = QMessageBox.question(
                self,
                "Rotate Page",
                "Rotating the page will clear all markers on this page. Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        if self.document_service.rotate_page(document, document.current_page_index, angle):
            self.show_page(document.current_page_index)
            self.statusBar().showMessage(f"Page rotated by {angle}°")
        else:
            self.statusBar().showMessage("Failed to rotate page")
            
    def toggle_crop_tool(self):
        """Toggle crop mode"""
        self.crop_mode = not self.crop_mode
        
        if self.crop_mode:
            # Start crop mode
            self.statusBar().showMessage("Crop Mode Active")
            self.crop_dialog = CropDialog(self)
            self.crop_dialog.finished.connect(self.finish_crop)
            self.crop_dialog.show()
            
            # Add initial crop rect
            self.add_crop_rect()
        else:
            # Cancel crop mode
            self.statusBar().showMessage("Crop Mode Cancelled")
            if self.crop_dialog:
                self.crop_dialog.close()
                self.crop_dialog = None
            self.remove_crop_rect()

    def add_crop_rect(self):
        """Add a resizable rectangle for cropping"""
        # Check if item exists and is valid
        if self.crop_rect_item:
            try:
                # If item is already in the scene, remove it
                if self.crop_rect_item.scene() == self.scene:
                    self.scene.removeItem(self.crop_rect_item)
            except RuntimeError:
                # Item was already deleted (e.g. by scene.clear())
                pass
            self.crop_rect_item = None
            
        # Default to center 50%
        scene_rect = self.scene.sceneRect()
        
        w = scene_rect.width() * 0.5
        h = scene_rect.height() * 0.5
        x = (scene_rect.width() - w) / 2
        y = (scene_rect.height() - h) / 2
        
        # Use dedicated CropRectItem
        self.crop_rect_item = CropRectItem(QRectF(0, 0, w, h))
        self.crop_rect_item.setPos(x, y)
        
        self.scene.addItem(self.crop_rect_item)
        
    def remove_crop_rect(self):
        if self.crop_rect_item:
            try:
                if self.crop_rect_item.scene() == self.scene:
                    self.scene.removeItem(self.crop_rect_item)
            except RuntimeError:
                # Item already deleted
                pass
            self.crop_rect_item = None
            
    def update_crop_ratio(self, ratio_name):
        """Update crop rect aspect ratio based on selection"""
        if not self.crop_rect_item:
            return
            
        try:
            # Calculate new height based on width and ratio
            rect = self.crop_rect_item.rect()
            width = rect.width()
            height = rect.height()
            
            ratio = None
            
            if ratio_name == "A4 (Portrait)":
                ratio = 1.414
                height = width * ratio
            elif ratio_name == "A4 (Landscape)":
                ratio = 1/1.414
                height = width * ratio
            elif ratio_name == "Letter (Portrait)":
                ratio = 1.294
                height = width * ratio
            elif ratio_name == "Letter (Landscape)":
                ratio = 1/1.294
                height = width * ratio
            
            # Set the aspect ratio on the item for enforcement during resize
            self.crop_rect_item.aspect_ratio = ratio
            
            self.crop_rect_item.setRect(QRectF(0, 0, width, height))
        except RuntimeError:
            self.crop_rect_item = None
        
    def finish_crop(self, result):
        """Apply crop if accepted"""
        if result == QDialog.Accepted and self.crop_rect_item:
            try:
                rect = self.crop_rect_item.sceneBoundingRect()
                x = int(rect.x())
                y = int(rect.y())
                w = int(rect.width())
                h = int(rect.height())
                
                document = self.document_service.get_current_document()
                if document:
                    if self.document_service.crop_page(document, document.current_page_index, x, y, w, h):
                        self.show_page(document.current_page_index)
                        self.statusBar().showMessage("Page cropped")
                    else:
                        self.statusBar().showMessage("Failed to crop page")
            except RuntimeError:
                self.statusBar().showMessage("Error: Crop selection lost")
        
        self.crop_mode = False
        self.remove_crop_rect()
        self.crop_dialog = None

    def toggle_ocr(self, checked):
        """Toggle OCR enabled state"""
        self.ocr_enabled = checked
        status = "enabled" if checked else "disabled"
        self.statusBar().showMessage(f"OCR {status} for next save/export")

    def open_ocr_language_dialog(self):
        """Open dialog to select OCR languages"""
        from .dialogs.ocr_language_dialog import OCRLanguageDialog
        
        dialog = OCRLanguageDialog(
            self, 
            available_languages=self.available_ocr_langs,
            selected_languages=self.selected_ocr_langs
        )
        
        if dialog.exec() == QDialog.Accepted:
            self.selected_ocr_langs = dialog.get_selected_languages()
            self.update_ocr_lang_tooltip()
            
    def update_ocr_lang_tooltip(self):
        """Update tooltip to show selected languages"""
        langs_str = "+".join(self.selected_ocr_langs)
        self.ocr_lang_btn.setToolTip(f"Selected Languages: {langs_str}")
        self.statusBar().showMessage(f"OCR Languages set to: {langs_str}")

    def delete_selected_marker(self):
        """Delete the currently selected marker(s)"""
        selected_items = self.scene.selectedItems()
        if not selected_items:
            return
            
        document = self.document_service.get_current_document()
        if not document:
            return
            
        page = document.get_current_page()
        if not page:
            return
            
        # Push undo state before deletion
        self.document_service.push_undo_state(document.current_page_index)
            
        for item in selected_items:
            if isinstance(item, ResizableRectItem):
                # Remove from model
                page.remove_rectangle(item._entity_id)
                # Remove from scene
                self.scene.removeItem(item)
        
        self.update_status_bar()

    def change_marker_color(self, color_name):
        """Update the current fill color and any selected markers"""
        if color_name in self.color_map:
            hex_color = self.color_map[color_name]
            self.fill_color = hex_color
            
            # Update selected items if any
            for item in self.scene.selectedItems():
                if isinstance(item, ResizableRectItem):
                    # Update visual item
                    item.setBrush(QBrush(QColor(hex_color)))
                    
                    # Update entity
                    document = self.document_service.get_current_document()
                    if document:
                        page = document.get_current_page()
                        if page:
                            rect_entity = page.get_rectangle(item._entity_id)
                            if rect_entity:
                                rect_entity.color = hex_color
    
    def change_quality(self, quality):
        """Update export quality setting"""
        self.output_quality = quality.lower()
        self.statusBar().showMessage(f"Export quality set to: {quality}")

    def open_document(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Document", "", "PDF Files (*.pdf);;All Files (*)"
        )
        if file_path:
            self._load_document_threaded(file_path)

    def _load_document_threaded(self, file_path):
        # Create progress dialog
        self._load_progress_dialog = QProgressDialog("Loading document...", "Cancel", 0, 100, self)
        self._load_progress_dialog.setWindowModality(Qt.WindowModal)
        self._load_progress_dialog.setWindowTitle("Loading")
        self._load_progress_dialog.setMinimumDuration(0)
        self._load_progress_dialog.setAutoClose(False)
        self._load_progress_dialog.setAutoReset(False)
        self._load_progress_dialog.setFixedSize(400, 120)

        # Create worker and thread
        self.loader_thread = QThread()
        self.loader_worker = DocumentLoaderWorker(self.document_service, file_path)
        self.loader_worker.moveToThread(self.loader_thread)

        # Connect signals
        self.loader_thread.started.connect(self.loader_worker.load_document)
        self.loader_worker.progress_update.connect(self._update_load_progress)
        self.loader_worker.page_loaded.connect(self._on_page_thumbnail_loaded)
        self.loader_worker.finished.connect(self._on_document_loaded)
        self.loader_worker.error.connect(self._on_load_error)
        
        # Cleanup
        self.loader_worker.finished.connect(self.loader_thread.quit)
        self.loader_worker.finished.connect(self.loader_worker.deleteLater)
        self.loader_thread.finished.connect(self.loader_thread.deleteLater)
        self._load_progress_dialog.canceled.connect(self.loader_worker.cancel)

        # Start
        self.page_list.clear()
        self.loader_thread.start()
        self._load_progress_dialog.show()

    def _update_load_progress(self, message, percentage):
        if hasattr(self, '_load_progress_dialog'):
            self._load_progress_dialog.setLabelText(message)
            self._load_progress_dialog.setValue(percentage)
        self.statusBar().showMessage(message)

    def _on_page_thumbnail_loaded(self, thumbnail_image, page_index):
        # Add thumbnail to list widget
        if thumbnail_image:
            icon = QIcon(QPixmap.fromImage(ImageQt(thumbnail_image)))
            item = QListWidgetItem(icon, f"Page {page_index + 1}")
            self.page_list.addItem(item)

    def _on_document_loaded(self, document):
        if hasattr(self, '_load_progress_dialog'):
            self._load_progress_dialog.close()
            delattr(self, '_load_progress_dialog')
        
        if document:
            self.show_page(0)
            self.update_status_bar()
            QMessageBox.information(self, "Success", f"Loaded document with {len(document.pages)} pages.")
        else:
            # Cancelled or failed silently (error signal handles failure)
            pass

    def _on_load_error(self, error_message):
        """Handle document loading errors"""
        if hasattr(self, '_load_progress_dialog'):
            self._load_progress_dialog.close()
            delattr(self, '_load_progress_dialog')
        QMessageBox.critical(self, "Error", f"Failed to open file: {error_message}")

    def show_page(self, page_num: int):
        document = self.document_service.get_current_document()
        if document and 0 <= page_num < document.page_count:
            self.document_service.navigate_to_page(document, page_num)
            
            # Reset crop_rect_item reference as scene.clear() will delete it
            self.crop_rect_item = None
            
            self.scene.clear()
            page = document.get_current_page()
            if page and page.image:
                self.scene.clear()
                qimage = ImageQt(page.image)
                pixmap = QPixmap.fromImage(qimage)
                self.scene.setSceneRect(QRectF(pixmap.rect())) # Force scene rect
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
                # Push undo state
                self.document_service.push_undo_state(document.current_page_index)
                
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

        # Use threaded export with progress dialog
        self._export_document_threaded(save_file_path)

    def _export_document_threaded(self, save_file_path):
        """Export document using background thread with enhanced progress dialog"""
        document = self.document_service.get_current_document()
        if not document:
            return

        # Create enhanced progress dialog
        self._export_progress_dialog = QProgressDialog("Exporting document...", "Cancel", 0, 100, self)
        self._export_progress_dialog.setWindowModality(Qt.WindowModal)
        self._export_progress_dialog.setWindowTitle("Export Progress")
        self._export_progress_dialog.setMinimumDuration(0)  # Show immediately
        self._export_progress_dialog.setAutoClose(False)
        self._export_progress_dialog.setAutoReset(False)
        self._export_progress_dialog.setFixedSize(400, 120)  # Fixed size for better appearance

        # Create worker and thread
        settings = {
            "ocr_enabled": self.ocr_enabled,
            "ocr_lang": "+".join(self.selected_ocr_langs), # Combine selected languages
            "output_quality": self.output_quality
        }

        self.export_thread = QThread()
        self.export_worker = ExportWorker(
            self.document_service,
            document,
            save_file_path,
            settings
        )

        # Move worker to thread
        self.export_worker.moveToThread(self.export_thread)

        # Connect signals
        self.export_thread.started.connect(self.export_worker.export_document)
        self.export_worker.progress_update.connect(self._update_export_progress)
        self.export_worker.finished.connect(self._on_export_finished)
        self.export_worker.error.connect(self._on_export_error)
        self.export_worker.finished.connect(self.export_thread.quit)
        self.export_worker.finished.connect(self.export_worker.deleteLater)
        self.export_thread.finished.connect(self.export_thread.deleteLater)
        self._export_progress_dialog.canceled.connect(self.export_worker.cancel)

        # Start the export
        self.export_thread.start()
        self._export_progress_dialog.show()

    def _update_export_progress(self, message, percentage):
        """Update export progress dialog and status bar"""
        if hasattr(self, '_export_progress_dialog'):
            self._export_progress_dialog.setLabelText(message)
            self._export_progress_dialog.setValue(percentage)
            # Update status bar with current operation
            self.statusBar().showMessage(f"Exporting: {message}")

    def _on_export_finished(self, success, message, file_path):
        """Handle export completion"""
        # Close progress dialog
        if hasattr(self, '_export_progress_dialog'):
            self._export_progress_dialog.close()
            delattr(self, '_export_progress_dialog')

        # Show result message
        if success:
            QMessageBox.information(self, "Export Successful", message)
        else:
            QMessageBox.critical(self, "Export Failed", message)

    def _on_export_error(self, error_message):
        """Handle export errors"""
        if hasattr(self, '_export_progress_dialog'):
            self._export_progress_dialog.close()
            delattr(self, '_export_progress_dialog')
        QMessageBox.critical(self, "Export Error", f"An error occurred during export:\n{error_message}")

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
            self._export_document_threaded(save_file_path)

    def about(self):
        QMessageBox.about(self, "About PyRedactor",
            "PyRedactor PDF Redaction Software\n\n"
            "Version 0.1.0\n"
            "Licensed under GPL V3.0\n\n"
            "©2025 Ernedin Zajko <ezajko@root.ba>")
            
    def undo(self):
        """Undo last action (marker change, crop, rotate)"""
        page_index = self.document_service.undo()
        if page_index is not None:
            self.show_page(page_index)
            self.statusBar().showMessage("Undo successful")
        else:
            self.statusBar().showMessage("Nothing to undo")
            
    def reset_document(self):
        """Reset document to original state (reload from disk)"""
        document = self.document_service.get_current_document()
        if document and document.file_path:
            reply = QMessageBox.question(
                self, "Reset Document",
                "Are you sure you want to reset the document? All unsaved changes will be lost.",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self._load_document_threaded(document.file_path)
        else:
             QMessageBox.warning(self, "Reset Document", "No document loaded to reset.")

    def trigger_batch_marker_operation(self, update_func, operation_name="Batch Operation"):
        """
        Trigger a batch marker/model operation in the background using BatchOperationWorker.
        update_func should be a callable that takes the document and performs updates.
        """
        document = self.document_service.get_current_document()
        if not document:
            QMessageBox.warning(self, "Batch Operation", "No document loaded.")
            return

        # Create enhanced progress dialog
        self._batch_progress_dialog = QProgressDialog(f"{operation_name} in progress...", "Cancel", 0, 100, self)
        self._batch_progress_dialog.setWindowModality(Qt.WindowModal)
        self._batch_progress_dialog.setWindowTitle(operation_name)
        self._batch_progress_dialog.setMinimumDuration(0)
        self._batch_progress_dialog.setAutoClose(False)
        self._batch_progress_dialog.setAutoReset(False)
        self._batch_progress_dialog.setFixedSize(400, 120)  # Fixed size for better appearance

        # Create worker and thread
        self.batch_thread = QThread()
        self.batch_worker = BatchOperationWorker(document, update_func, operation_name)

        # Move worker to thread
        self.batch_worker.moveToThread(self.batch_thread)

        # Connect signals
        self.batch_thread.started.connect(self.batch_worker.execute_batch_operation)
        self.batch_worker.progress_update.connect(self._update_batch_progress)
        self.batch_worker.finished.connect(self._on_batch_finished)
        self.batch_worker.error.connect(self._on_batch_error)
        self.batch_worker.finished.connect(self.batch_thread.quit)
        self.batch_worker.finished.connect(self.batch_worker.deleteLater)
        self.batch_thread.finished.connect(self.batch_thread.deleteLater)
        self._batch_progress_dialog.canceled.connect(self.batch_worker.cancel)

        # Start the batch operation
        self.batch_thread.start()
        self._batch_progress_dialog.show()

    def _update_batch_progress(self, message, percentage):
        """Update batch operation progress dialog and status bar"""
        if hasattr(self, '_batch_progress_dialog'):
            self._batch_progress_dialog.setLabelText(message)
            self._batch_progress_dialog.setValue(percentage)
            # Update status bar with current operation
            self.statusBar().showMessage(f"Batch Operation: {message}")

    def _on_batch_finished(self, success, message):
        """Handle batch operation completion"""
        # Close progress dialog
        if hasattr(self, '_batch_progress_dialog'):
            self._batch_progress_dialog.close()
            delattr(self, '_batch_progress_dialog')

        # Show result message
        if success:
            QMessageBox.information(self, "Batch Operation", message)
            # Optionally refresh the UI
            document = self.document_service.get_current_document()
            if document:
                self.show_page(document.current_page_index)
        else:
            QMessageBox.critical(self, "Batch Operation", message)

    def _on_batch_error(self, error_message):
        """Handle batch operation errors"""
        if hasattr(self, '_batch_progress_dialog'):
            self._batch_progress_dialog.close()
            delattr(self, '_batch_progress_dialog')
        QMessageBox.critical(self, "Batch Operation Error", f"An error occurred during batch operation:\n{error_message}")

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

    def toggle_enhancement_options(self):
        """Toggle image enhancement options dialog"""
        from .dialogs.enhancement_options_dialog import EnhancementOptionsDialog

        dialog = EnhancementOptionsDialog(
            self,
            enhancement_enabled=self.enhancement_enabled,
            brightness=self.enhancement_brightness,
            contrast=self.enhancement_contrast,
            sharpness=self.enhancement_sharpness,
            auto_level=self.enhancement_auto_level,
            deskew=self.enhancement_deskew,
            denoise=self.enhancement_denoise
        )

        if dialog.exec() == QDialog.Accepted:
            values = dialog.get_values()
            self.enhancement_enabled = values["enhancement_enabled"]
            self.enhancement_brightness = values["brightness"]
            self.enhancement_contrast = values["contrast"]
            self.enhancement_sharpness = values["sharpness"]
            self.enhancement_auto_level = values["auto_level"]
            self.enhancement_deskew = values["deskew"]
            self.enhancement_denoise = values["denoise"]

            # Pass settings to document repository
            if hasattr(self.document_service, "document_repository"):
                self.document_service.document_repository.set_enhancement_settings(
                    enabled=self.enhancement_enabled,
                    brightness=self.enhancement_brightness,
                    contrast=self.enhancement_contrast,
                    sharpness=self.enhancement_sharpness,
                    auto_level=self.enhancement_auto_level,
                    deskew=self.enhancement_deskew,
                    denoise=self.enhancement_denoise
                )

            # Show status message
            if self.enhancement_enabled:
                self.statusBar().showMessage("Image enhancement enabled")
            else:
                self.statusBar().showMessage("Image enhancement disabled")

            # Ask to reload if document is open
            document = self.document_service.get_current_document()
            if document and document.file_path:
                reply = QMessageBox.question(
                    self, 
                    "Reload Document?",
                    "Enhancement settings have changed. Do you want to reload the document to apply them?\n\n"
                    "Note: This will clear current markers.",
                    QMessageBox.Yes | QMessageBox.No, 
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    self._load_document_threaded(document.file_path)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    sys.exit(app.exec())
