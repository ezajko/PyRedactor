#!/usr/bin/env python3
# Licensed under GPLV3.0
# (c) 2025 Ernedin Zajko <ezajko@root.ba>

"""
Graphics Items for PyRedactor Application
"""

from PySide6.QtWidgets import QGraphicsRectItem, QRubberBand, QGraphicsView, QApplication
from PySide6.QtGui import QBrush, QPen, QColor
from PySide6.QtCore import Qt, QPoint, QRect, QRectF, QSize


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
            
            # Check if parent has enforced aspect ratio
            aspect_ratio = getattr(parent, 'aspect_ratio', None)

            if self.position == "top_left":
                new_rect.setTopLeft(new_rect.topLeft() + delta)
                if aspect_ratio:
                    # Adjust width to match height * ratio, or vice versa depending on drag
                    # For simplicity, let's drive width by height change
                    h = new_rect.height()
                    w = h / aspect_ratio
                    new_rect.setLeft(new_rect.right() - w)
                    
            elif self.position == "top_right":
                new_rect.setTopRight(new_rect.topRight() + delta)
                if aspect_ratio:
                    h = new_rect.height()
                    w = h / aspect_ratio
                    new_rect.setRight(new_rect.left() + w)
                    
            elif self.position == "bottom_left":
                new_rect.setBottomLeft(new_rect.bottomLeft() + delta)
                if aspect_ratio:
                    h = new_rect.height()
                    w = h / aspect_ratio
                    new_rect.setLeft(new_rect.right() - w)
                    
            elif self.position == "bottom_right":
                new_rect.setBottomRight(new_rect.bottomRight() + delta)
                if aspect_ratio:
                    h = new_rect.height()
                    w = h / aspect_ratio
                    new_rect.setRight(new_rect.left() + w)
            
            # Ensure positive width/height
            if new_rect.width() < 10: new_rect.setWidth(10)
            if new_rect.height() < 10: new_rect.setHeight(10)
            
            parent.setRect(new_rect)
            parent.update_handles()
            parent.update()
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            parent = self.parentItem()
            if hasattr(parent, "update_data_model_from_rect"):
                parent.update_data_model_from_rect()
            
            # Always update handles and redraw
            parent.update_handles()
            parent.update()
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
        elif change == QGraphicsRectItem.ItemPositionHasChanged:
            # Sync position to data model after move
            self.update_data_model_from_rect()
            self.update_handles()
        return super().itemChange(change, value)

    def setRect(self, rect):
        super().setRect(rect)
        self.update_handles()
        self.update_data_model_from_rect()
        self.update()
        self.update_data_model_from_rect()

    def update_data_model_from_rect(self):
        """
        Update the corresponding RectangleEntity in the data model
        to match the current geometry and position of this QGraphicsRectItem.
        """
        scene = self.scene()
        if scene is None or not scene.views():
            return
        main_window = scene.views()[0].window()
        if main_window and hasattr(main_window, 'document_service'):
            document = main_window.document_service.get_current_document()
            if document:
                page = document.get_current_page()
                if page:
                    rect = self.rect()
                    pos = self.pos()
                    start_point = (rect.topLeft().x() + pos.x(), rect.topLeft().y() + pos.y())
                    end_point = (rect.bottomRight().x() + pos.x(), rect.bottomRight().y() + pos.y())
                    rectangle_entity = page.get_rectangle(self._entity_id)
                    if rectangle_entity:
                        rectangle_entity.start_point = start_point
                        rectangle_entity.end_point = end_point
                    # Optionally, call the redaction_service to keep logic centralized
                    # (Do not call resize_redaction_rectangle here, as we are directly updating the model)


class CropRectItem(QGraphicsRectItem):
    """
    A specialized graphics item for the crop tool.
    It does not interact with the data model (RectangleEntity).
    """
    def __init__(self, rect):
        super().__init__(rect)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsRectItem.ItemIsMovable, True)
        self.setFlag(QGraphicsRectItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        
        # Distinctive style for crop tool
        self.setPen(QPen(QColor(Qt.blue), 2, Qt.DashLine))
        self.setBrush(QBrush(QColor(0, 0, 255, 30))) # Light blue transparent fill
        
        self.handles = [
            HandleItem(self, pos)
            for pos in ("top_left", "top_right", "bottom_left", "bottom_right")
        ]
        self.update_handles()
        
        # Aspect ratio (height / width). None means free resize.
        self.aspect_ratio = None 

    def update_handles(self):
        rect = self.rect()
        positions = [rect.topLeft(), rect.topRight(), rect.bottomLeft(), rect.bottomRight()]
        for handle, pos in zip(self.handles, positions):
            handle.setPos(pos)
            handle.setVisible(True) # Always visible for crop tool
            handle.setZValue(10000)
            handle.setAcceptHoverEvents(True)
            handle.setAcceptedMouseButtons(Qt.LeftButton)

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.ItemPositionHasChanged:
            self.update_handles()
        return super().itemChange(change, value)
        
    def setRect(self, rect):
        super().setRect(rect)
        self.update_handles()


class PhotoViewer(QGraphicsView):
    def __init__(self, parent):
        super().__init__(parent)
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.setMouseTracking(True)
        self.origin = QPoint()
        self.current_rect_item = None
        self._panning = False
        self._pan_start = QPoint()

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._panning = True
            self._pan_start = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return

        # If clicking on a handle or existing item, let the scene handle it
        # But ignore the background pixmap (which is a QGraphicsPixmapItem)
        item = self.scene().itemAt(self.mapToScene(event.pos()), self.transform())
        if item and (isinstance(item, HandleItem) or isinstance(item, ResizableRectItem) or isinstance(item, CropRectItem)):
            super().mousePressEvent(event)
            return

        # If in crop mode, do not allow drawing new redaction rectangles
        if hasattr(self.window(), 'crop_mode') and self.window().crop_mode:
            super().mousePressEvent(event)
            return

        if event.button() == Qt.LeftButton:
            self.origin = event.pos()
            self.rubberBand.setGeometry(QRect(self.origin, QSize()))
            self.rubberBand.show()

    def mouseMoveEvent(self, event):
        if self._panning:
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return

        if not self.rubberBand.isHidden():
            self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return

        if not self.rubberBand.isHidden():
            self.rubberBand.hide()
            rect = self.rubberBand.geometry()
            
            # Ensure rect has some size
            if rect.width() < 5 or rect.height() < 5:
                print("Debug: Rect too small, ignoring")
                super().mouseReleaseEvent(event)
                return

            scene_rect = self.mapToScene(rect).boundingRect()
            print(f"Debug: Creating marker at {scene_rect}")
            
            # Create redaction via service
            main_window = self.window()
            if main_window and hasattr(main_window, 'redaction_service'):
                document = main_window.document_service.get_current_document()
                if document:
                    page = document.get_current_page()
                    if page:
                        try:
                            # Add to model
                            new_rect = main_window.redaction_service.add_redaction_rectangle(
                                page, 
                                (scene_rect.left(), scene_rect.top()), 
                                (scene_rect.right(), scene_rect.bottom()),
                                color=main_window.fill_color
                            )
                            
                            if new_rect:
                                # Add to scene
                                width = scene_rect.width()
                                height = scene_rect.height()
                                rect_item = ResizableRectItem(QRectF(0, 0, width, height), entity_id=new_rect.id)
                                rect_item.setPos(scene_rect.left(), scene_rect.top())
                                rect_item.setBrush(QBrush(QColor(main_window.fill_color)))
                                rect_item.setOpacity(0.5)
                                self.scene().addItem(rect_item)
                                
                                main_window.update_status_bar()
                            else:
                                print("Error: Failed to create redaction rectangle in model")
                        except Exception as e:
                            print(f"Error creating marker: {e}")

        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            zoom_in = event.angleDelta().y() > 0
            if zoom_in:
                self.scale(1.1, 1.1)
            else:
                self.scale(0.9, 0.9)
        else:
            super().wheelEvent(event)
