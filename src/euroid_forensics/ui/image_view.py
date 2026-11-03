"""Scene-coordinate viewing and explicit pixel-space region selection."""

import math

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView

from euroid_forensics.domain.models import Region
from euroid_forensics.image_processing.loading import ImageAsset


class ImageView(QGraphicsView):
    region_changed = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScene(QGraphicsScene(self))
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setMinimumSize(300, 300)
        self.setAccessibleName("Image viewer: drag to pan; wheel to zoom")
        self.asset = None
        self.region = None
        self.selecting = False
        self._start = None
        self._selection = None
        self._boundary = None
        self._fit = True
        self.show_empty()

    def show_empty(self):
        self.scene().clear()
        self._selection = self._boundary = None
        self.asset = self.region = None
        text = self.scene().addText(
            "No image loaded\n\nChoose a JPG / PNG or load the synthetic demo"
        )
        text.setDefaultTextColor(QColor("#8395aa"))
        self.scene().setSceneRect(QRectF(0, 0, 550, 360))
        text.setPos(40, 140)
        self.resetTransform()

    def set_asset(self, asset: ImageAsset):
        self.scene().clear()
        self._selection = self._boundary = None
        self.region = None
        self.asset = asset
        # QPixmap takes its own pixel storage. Keep the asset alive while the
        # QImage borrows its contiguous BGR buffer; no RGB conversion/copy needed.
        image = QImage(
            asset.bgr.data,
            asset.width,
            asset.height,
            asset.bgr.strides[0],
            QImage.Format.Format_BGR888,
        )
        self.scene().addPixmap(QPixmap.fromImage(image))
        self.scene().setSceneRect(QRectF(0, 0, asset.width, asset.height))
        self.fit_image()

    def fit_image(self):
        self._fit = True
        self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def zoom(self, factor: float):
        value = self.transform().m11() * factor
        if 0.03 <= value <= 12:
            self._fit = False
            self.scale(factor, factor)

    def wheelEvent(self, event):
        self.zoom(1.2 if event.angleDelta().y() > 0 else 1 / 1.2)
        event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._fit:
            self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def set_selection_mode(self, enabled: bool):
        self.selecting = enabled
        self.setDragMode(
            QGraphicsView.DragMode.NoDrag if enabled else QGraphicsView.DragMode.ScrollHandDrag
        )
        self.setCursor(Qt.CursorShape.CrossCursor if enabled else Qt.CursorShape.OpenHandCursor)

    def set_region(self, region: Region | None):
        if region and self.asset:
            region.validate(self.asset.width, self.asset.height)
        if self._selection:
            self.scene().removeItem(self._selection)
            self._selection = None
        self.region = region
        if region:
            pen = QPen(QColor("#5ba8ff"), 2)
            pen.setCosmetic(True)
            self._selection = self.scene().addRect(
                QRectF(region.x, region.y, region.width, region.height),
                pen,
                QColor(70, 140, 255, 35),
            )
            self._selection.setZValue(3)
        self.region_changed.emit(region)

    def set_boundary(self, points=()):
        if self._boundary:
            self.scene().removeItem(self._boundary)
            self._boundary = None
        if points:
            pen = QPen(QColor("#2dd4a8"), 2, Qt.PenStyle.DashLine)
            pen.setCosmetic(True)
            self._boundary = self.scene().addPolygon(
                QPolygonF([QPointF(x, y) for x, y in points]),
                pen,
            )
            self._boundary.setZValue(2)

    def mousePressEvent(self, event):
        if self.selecting and self.asset and event.button() == Qt.MouseButton.LeftButton:
            self._start = self.mapToScene(event.position().toPoint())
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._start is not None:
            if self._selection:
                self.scene().removeItem(self._selection)
            rect = QRectF(self._start, self.mapToScene(event.position().toPoint())).normalized()
            rect = rect.intersected(self.sceneRect())
            pen = QPen(QColor("#5ba8ff"), 2)
            pen.setCosmetic(True)
            self._selection = self.scene().addRect(rect, pen, QColor(70, 140, 255, 35))
            self._selection.setZValue(3)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._start is not None:
            rect = QRectF(self._start, self.mapToScene(event.position().toPoint())).normalized()
            rect = rect.intersected(self.sceneRect())
            self._start = None
            x, y = max(0, math.floor(rect.x())), max(0, math.floor(rect.y()))
            width = min(self.asset.width, math.ceil(rect.right())) - x
            height = min(self.asset.height, math.ceil(rect.bottom())) - y
            # An undersized drag clears selection rather than silently analyzing a tiny crop.
            self.set_region(Region(x, y, width, height) if min(width, height) >= 32 else None)
            event.accept()
        else:
            super().mouseReleaseEvent(event)
