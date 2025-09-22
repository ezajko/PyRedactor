#!/usr/bin/env python3
# Licensed under GPLV3.0
# (c) 2025 Ernedin Zajko <ezajko@root.ba>

"""
Graphics Items for PyRedactor Application
"""

from PySide6.QtWidgets import QGraphicsRectItem, QRubberBand, QGraphicsView, QApplication
from PySide6.QtGui import QBrush, QPen, QColor
from PySide6.QtCore import Qt, QPoint, QRect, QRectF


class HandleItem(QGraphicsRectItem):
    def __init__(self, parent, position):
        super().__init__(-8, -8, 16, 16, parent)
        self.position = position
        self.setBrush(QBrush(QColor("white")))
        self.setPen(QPen(QColor("black"), 2))
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable, False)
        self.setZValue(10000)

    def hoverEnterEvent(self, event):
        if self.position in ("top_left", "bottom_right"):
            self.setCursor(Qt.SizeFDiagCursor)
        else:
            self.setCursor(Qt.SizeBDiagCursor)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.unsetCursor()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start_pos = event.scenePos()
            self._orig_rect = self.parentItem().rect()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            parent = self.parentItem()
            orig_rect = self._orig_rect
            delta = event.scenePos() - self._drag_start_pos
            new_rect = QRectF(orig_rect)
            if self.position == "top_left":
                new_rect.setTopLeft(new_rect.topLeft() + delta)
            elif self.position == "top_right":
                new_rect.setTopRight(new_rect.topRight() + delta)
            elif self.position == "bottom_left":
                new_rect.setBottomLeft(new_rect.bottomLeft() + delta)
            elif self.position == "bottom_right":
                new_rect.setBottomRight(new_rect.bottomRight() + delta)
            parent.setRect(new_rect)
            parent.update_handles()
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            parent = self.parentItem()
            if hasattr(parent, "update_data_model_from_rect"):
                parent.update_data_model_from_rect()
            event.accept()


class ResizableRectItem(QGraphicsRectItem):
    def __init__(self, rect, entity_id):
        super().__init__(rect)
        self._entity_id = entity_id
        self.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsRectItem.ItemIsMovable, True)
        self.setFlag(QGraphicsRectItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.setPen(QPen(QColor("black"), 1, Qt.DashLine))
        self.handles = [
            HandleItem(self, pos)
            for pos in ("top_left", "top_right", "bottom_left", "bottom_right")
        ]
        self.update_handles()

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        if self.isSelected():
            pen = QPen(QColor(Qt.blue), 5, Qt.DotLine)
            painter.setPen(pen)
            painter.drawRect(self.rect())

    def update_handles(self):
        rect = self.rect()
        positions = [rect.topLeft(), rect.topRight(), rect.bottomLeft(), rect.bottomRight()]
        for handle, pos in zip(self.handles, positions):
            handle.setPos(pos)
            handle.setVisible(self.isSelected())
            handle.setZValue(10000)
            handle.setAcceptHoverEvents(True)
            handle.setAcceptedMouseButtons(Qt.LeftButton)

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.ItemSelectedChange:
            # Always keep marker selectable
            self.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
            self.update_handles()
        return super().itemChange(change, value)

    def setRect(self, rect):
        super().setRect(rect)
        self.update_handles()

    def update_data_model_from_rect(self):
        main_window = self.scene().views()[0].window()
        if main_window and hasattr(main_window, 'document_service'):
            document = main_window.document_service.get_current_document()
            if document:
                page = document.get_current_page()
                if page:
                    rect = self.rect()
                    start_point = (rect.topLeft().x(), rect.topLeft().y())
                    end_point = (rect.bottomRight().x(), rect.bottomRight().y())
                    rectangle_entity = page.get_rectangle(self._entity_id)
                    if rectangle_entity:
                        rectangle_entity.start_point = start_point
                        rectangle_entity.end_point = end_point
                    if hasattr(main_window, 'redaction_service'):
                        main_window.redaction_service.resize_redaction_rectangle(
                            page, self._entity_id, rect.width(), rect.height()
                        )
    def update_data_model_from_rect(self):
        """
        Update the corresponding RectangleEntity in the data model
        to match the current geometry of this QGraphicsRectItem.
        """
        main_window = self.scene().views()[0].window()
        if main_window and hasattr(main_window, 'document_service'):
            document = main_window.document_service.get_current_document()
            if document:
                page = document.get_current_page()
                if page:
                    rect = self.rect()
                    start_point = (rect.topLeft().x(), rect.topLeft().y())
                    end_point = (rect.bottomRight().x(), rect.bottomRight().y())
                    # Update the RectangleEntity directly
                    rectangle_entity = page.get_rectangle(self._entity_id)
                    if rectangle_entity:
                        rectangle_entity.start_point = start_point
                        rectangle_entity.end_point = end_point
                    # Optionally, call the redaction_service to keep logic centralized
                    if hasattr(main_window, 'redaction_service'):
                        main_window.redaction_service.resize_redaction_rectangle(
                            page, self._entity_id, rect.width(), rect.height()
                        )




class PhotoViewer(QGraphicsView):
    def __init__(self, parent):
        super().__init__(parent)
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.setMouseTracking(True)
        self.origin = QPoint()
        self.setAcceptDrops(True)  # Enable drag and drop

    def mousePressEvent(self, event):
        print(f"[DEBUG] PhotoViewer: mousePressEvent called.")
        if event.button() == Qt.LeftButton:
            item = self.itemAt(event.pos())
            # If click is on a handle, let the handle handle it
            if isinstance(item, HandleItem):
                QGraphicsView.mousePressEvent(self, event)
                return
            # If click is on a marker, select it and let QGraphicsView handle move
            elif isinstance(item, ResizableRectItem):
                # Deselect all others first
                for marker in self.scene().items():
                    if isinstance(marker, ResizableRectItem) and marker is not item:
                        marker.setSelected(False)
                item.setSelected(True)
                # --- Update handles for all markers after selection change ---
                for marker in self.scene().items():
                    if isinstance(marker, ResizableRectItem):
                        marker.update_handles()
                QGraphicsView.mousePressEvent(self, event)
                return
            # If click is on empty space, deselect all and start rubber band for creation
            else:
                for marker in self.scene().items():
                    if isinstance(marker, ResizableRectItem):
                        marker.setSelected(False)
                # --- Update handles for all markers after deselection ---
                for marker in self.scene().items():
                    if isinstance(marker, ResizableRectItem):
                        marker.update_handles()
                self.origin = event.pos()
                self.rubberBand.setGeometry(QRect(self.origin, self.origin).normalized())
                self.rubberBand.show()
        else:
            QGraphicsView.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        if not self.origin.isNull() and self.rubberBand.isVisible():
            self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.rubberBand.hide()
            # Only allow marker creation if NOT in edit mode
            if not getattr(self, '_edit_mode_active', False):
                if not self.origin.isNull() and (self.mapToScene(self.origin) != self.mapToScene(event.pos())):
                    end_point = event.pos()
                    start_scene_point = self.mapToScene(self.origin)
                    end_scene_point = self.mapToScene(end_point)

                    rect = QRectF(start_scene_point, end_scene_point).normalized()
                    start_scene_point = rect.topLeft()
                    end_scene_point = rect.bottomRight()

                    rect_width = end_scene_point.x() - start_scene_point.x()
                    rect_height = end_scene_point.y() - start_scene_point.y()

                    main_window = self.window()
                    color = main_window.fill_color if main_window else "black"

                    # Convert scene coordinates to image coordinates
                    # This is a simplification and might need adjustment based on image scaling and position
                    start_img_point = (start_scene_point.x(), start_scene_point.y())
                    end_img_point = (end_scene_point.x(), end_scene_point.y())

                    from ..core.entities.rectangle import RectangleEntity
                    import uuid
                    new_rect_id = str(uuid.uuid4())
                    rect_entity = RectangleEntity(new_rect_id, start_img_point, end_img_point, color)

                    print(f"[DEBUG] PhotoViewer: Creating ResizableRectItem with rect={rect}, entity_id={rect_entity.id}")
                    rect_item = ResizableRectItem(rect, entity_id=rect_entity.id)
                    rect_item.setBrush(QBrush(QColor(color).lighter(120))) # Make it slightly lighter
                    rect_item.setOpacity(0.5) # 50% transparency
                    self.scene().addItem(rect_item)

                    if main_window and hasattr(main_window, 'document_service') and main_window.document_service.get_current_document():
                        document = main_window.document_service.get_current_document()
                        page = document.get_current_page()
                        if page:
                            page.add_rectangle(rect_entity)

            self.origin = QPoint()
        super().mouseReleaseEvent(event)

    def dragEnterEvent(self, event):
        """Handle drag enter events"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """Handle file drop events"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                if file_path:
                    # Open the dropped file
                    main_window = self.window()
                    if main_window:
                        main_window.open_file_with_path(file_path)
                    event.acceptProposedAction()
