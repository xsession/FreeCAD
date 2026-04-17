"""2D schematic editor with connector symbol placement, wire drawing, and grid.

Provides a QGraphicsView-based canvas for placing connector symbols, drawing
wires between pin endpoints, and editing net connectivity interactively.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from PySide import QtCore, QtGui

# ── Constants ────────────────────────────────────────────────────

GRID_SIZE = 20
SYMBOL_WIDTH = 60
SYMBOL_HEIGHT = 40
PIN_RADIUS = 4
PIN_SPACING = 16

GRID_PEN = QtGui.QPen(QtGui.QColor(220, 220, 220), 0.5)
CONNECTOR_BRUSH = QtGui.QBrush(QtGui.QColor(200, 220, 255))
CONNECTOR_PEN = QtGui.QPen(QtGui.QColor(40, 80, 160), 1.5)
PIN_BRUSH = QtGui.QBrush(QtGui.QColor(255, 100, 80))
PIN_HOVER_BRUSH = QtGui.QBrush(QtGui.QColor(255, 200, 60))
WIRE_PEN = QtGui.QPen(QtGui.QColor(60, 60, 60), 1.5)
WIRE_SELECTED_PEN = QtGui.QPen(QtGui.QColor(255, 120, 0), 2.5)
SELECTION_PEN = QtGui.QPen(QtGui.QColor(0, 120, 255), 2.0, QtCore.Qt.DashLine)

# ── Helper: snap to grid ────────────────────────────────────────


def snap(value: float, grid: int = GRID_SIZE) -> float:
    return round(value / grid) * grid


# ── Pin item ─────────────────────────────────────────────────────


class PinItem(QtGui.QGraphicsEllipseItem):
    """Clickable pin circle that can be wired to another pin."""

    def __init__(self, pin_id: str, parent: "ConnectorSymbol") -> None:
        super().__init__(-PIN_RADIUS, -PIN_RADIUS, PIN_RADIUS * 2, PIN_RADIUS * 2, parent)
        self.pin_id = pin_id
        self.setBrush(PIN_BRUSH)
        self.setPen(QtGui.QPen(QtCore.Qt.NoPen))
        self.setAcceptHoverEvents(True)
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
        self.setToolTip(pin_id)

    def hoverEnterEvent(self, event) -> None:
        self.setBrush(PIN_HOVER_BRUSH)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        self.setBrush(PIN_BRUSH)
        super().hoverLeaveEvent(event)


# ── Connector symbol ─────────────────────────────────────────────


class ConnectorSymbol(QtGui.QGraphicsItemGroup):
    """Visual representation of a connector on the schematic canvas."""

    def __init__(
        self,
        connector_id: str,
        reference: str,
        pin_ids: List[str],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.connector_id = connector_id
        self.reference = reference
        self.pin_items: Dict[str, PinItem] = {}

        # Compute body size
        height = max(SYMBOL_HEIGHT, PIN_SPACING * (len(pin_ids) + 1))
        body = QtGui.QGraphicsRectItem(0, 0, SYMBOL_WIDTH, height, self)
        body.setBrush(CONNECTOR_BRUSH)
        body.setPen(CONNECTOR_PEN)

        # Ref designator label
        label = QtGui.QGraphicsSimpleTextItem(reference, self)
        label.setPos(4, 2)

        # Pin circles along left edge
        for i, pin_id in enumerate(pin_ids):
            pin = PinItem(pin_id, self)
            y_pos = PIN_SPACING * (i + 1)
            pin.setPos(0, y_pos)
            self.pin_items[pin_id] = pin

            # Label the cavity name (last portion of pin_id or full)
            pin_label = QtGui.QGraphicsSimpleTextItem(pin_id.split(":")[-1], self)
            pin_label.setPos(PIN_RADIUS + 4, y_pos - 6)
            pin_label.setScale(0.7)

        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)

    def pin_scene_pos(self, pin_id: str) -> Optional[QtCore.QPointF]:
        item = self.pin_items.get(pin_id)
        if item:
            return item.mapToScene(0, 0)
        return None


# ── Wire line ────────────────────────────────────────────────────


class WireLine(QtGui.QGraphicsLineItem):
    """Drawn wire connecting two pins."""

    def __init__(self, wire_id: str, from_pin: PinItem, to_pin: PinItem) -> None:
        super().__init__()
        self.wire_id = wire_id
        self.from_pin = from_pin
        self.to_pin = to_pin
        self.setPen(WIRE_PEN)
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
        self.update_positions()

    def update_positions(self) -> None:
        p1 = self.from_pin.mapToScene(0, 0)
        p2 = self.to_pin.mapToScene(0, 0)
        self.setLine(p1.x(), p1.y(), p2.x(), p2.y())


# ── Schematic scene ──────────────────────────────────────────────


class SchematicScene(QtGui.QGraphicsScene):
    """Scene with snapping grid and symbol management."""

    pinClicked = QtCore.Signal(str)  # emits pin_id
    wireCreated = QtCore.Signal(str, str)  # from_pin_id, to_pin_id

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setSceneRect(0, 0, 2000, 1500)
        self.connector_symbols: Dict[str, ConnectorSymbol] = {}
        self.wire_lines: Dict[str, WireLine] = {}
        self._pending_pin: Optional[PinItem] = None
        self._rubber_line: Optional[QtGui.QGraphicsLineItem] = None

    def drawBackground(self, painter: QtGui.QPainter, rect: QtCore.QRectF) -> None:
        painter.fillRect(rect, QtGui.QColor(255, 255, 255))
        left = int(rect.left()) - (int(rect.left()) % GRID_SIZE)
        top = int(rect.top()) - (int(rect.top()) % GRID_SIZE)
        painter.setPen(GRID_PEN)
        x = left
        while x < rect.right():
            painter.drawLine(QtCore.QPointF(x, rect.top()), QtCore.QPointF(x, rect.bottom()))
            x += GRID_SIZE
        y = top
        while y < rect.bottom():
            painter.drawLine(QtCore.QPointF(rect.left(), y), QtCore.QPointF(rect.right(), y))
            y += GRID_SIZE

    def add_connector_symbol(
        self,
        connector_id: str,
        reference: str,
        pin_ids: List[str],
        x: float = 0.0,
        y: float = 0.0,
    ) -> ConnectorSymbol:
        sym = ConnectorSymbol(connector_id, reference, pin_ids)
        sym.setPos(snap(x), snap(y))
        self.addItem(sym)
        self.connector_symbols[connector_id] = sym
        return sym

    def add_wire_line(
        self,
        wire_id: str,
        from_pin_id: str,
        to_pin_id: str,
    ) -> Optional[WireLine]:
        from_item = self._find_pin_item(from_pin_id)
        to_item = self._find_pin_item(to_pin_id)
        if from_item and to_item:
            wire = WireLine(wire_id, from_item, to_item)
            self.addItem(wire)
            self.wire_lines[wire_id] = wire
            return wire
        return None

    def refresh_wires(self) -> None:
        """Update all wire positions after connector move."""
        for wire in self.wire_lines.values():
            wire.update_positions()

    def remove_connector(self, connector_id: str) -> None:
        sym = self.connector_symbols.pop(connector_id, None)
        if sym:
            self.removeItem(sym)

    def _find_pin_item(self, pin_id: str) -> Optional[PinItem]:
        for sym in self.connector_symbols.values():
            if pin_id in sym.pin_items:
                return sym.pin_items[pin_id]
        return None

    # ── interactive wire-drawing mode ────────────────────────────

    def mousePressEvent(self, event: QtGui.QGraphicsSceneMouseEvent) -> None:
        item = self.itemAt(event.scenePos())
        if isinstance(item, PinItem):
            if self._pending_pin is None:
                # Start drawing a wire from this pin
                self._pending_pin = item
                self._rubber_line = QtGui.QGraphicsLineItem()
                self._rubber_line.setPen(SELECTION_PEN)
                p = item.mapToScene(0, 0)
                self._rubber_line.setLine(p.x(), p.y(), p.x(), p.y())
                self.addItem(self._rubber_line)
                self.pinClicked.emit(item.pin_id)
                return
            else:
                # Complete wire: second pin clicked
                self.wireCreated.emit(self._pending_pin.pin_id, item.pin_id)
                self._cleanup_rubber()
                return
        # Normal event handling (moves, selects)
        self._cleanup_rubber()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QGraphicsSceneMouseEvent) -> None:
        if self._rubber_line and self._pending_pin:
            p = self._pending_pin.mapToScene(0, 0)
            mp = event.scenePos()
            self._rubber_line.setLine(p.x(), p.y(), mp.x(), mp.y())
        super().mouseMoveEvent(event)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == QtCore.Qt.Key_Escape:
            self._cleanup_rubber()
        super().keyPressEvent(event)

    def _cleanup_rubber(self) -> None:
        if self._rubber_line:
            self.removeItem(self._rubber_line)
            self._rubber_line = None
        self._pending_pin = None


# ── Schematic editor widget ──────────────────────────────────────


class SchematicEditorWidget(QtGui.QGraphicsView):
    """Top-level widget for 2-D harness schematic editing."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._scene = SchematicScene(self)
        self.setScene(self._scene)
        self.setDragMode(QtGui.QGraphicsView.RubberBandDrag)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setTransformationAnchor(QtGui.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtGui.QGraphicsView.AnchorUnderMouse)

    @property
    def schematic_scene(self) -> SchematicScene:
        return self._scene

    def add_marker(self, x: float, y: float, text: str) -> None:
        """Legacy compatibility — add a text marker at (x, y)."""
        self._scene.addText(text).setPos(x, y)

    def wheelEvent(self, event) -> None:
        """Zoom with Ctrl+Scroll."""
        factor = 1.15 if event.delta() > 0 else 1.0 / 1.15
        self.scale(factor, factor)

    def populate_from_model(self, model) -> None:
        """Create connector symbols and wire lines from a project model."""
        col = 0
        for conn in model.connectors.values():
            pin_ids = model.connector_pin_ids(conn.connector_instance_id)
            self._scene.add_connector_symbol(
                conn.connector_instance_id,
                conn.reference,
                pin_ids,
                x=100 + col * 140,
                y=100,
            )
            col += 1

        for wire in model.wires.values():
            self._scene.add_wire_line(wire.wire_id, wire.from_pin_id, wire.to_pin_id)
