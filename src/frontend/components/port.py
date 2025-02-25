# src/components/port.py
from PyQt5.QtWidgets import QGraphicsItem
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .base import WorkflowComponent

class Port(QGraphicsItem):
    def __init__(self, name: str, port_type: str, position: QPointF, 
                 is_output: bool = False, parent: Optional['WorkflowComponent'] = None):
        super().__init__(parent)
        self.name = name
        self.port_type = port_type
        self.is_output = is_output
        self.setPos(position)
        self._parent = parent
        
        # Visual properties
        self.radius = 5
        self.color = QColor("#4ade80") if is_output else QColor("#60a5fa")
        self.hover_color = QColor("#3b82f6")
        self.hovered = False
        
        # Setup flags
        self.setAcceptHoverEvents(True)
        
    def boundingRect(self):
        return QRectF(-self.radius, -self.radius, 
                     self.radius * 2, self.radius * 2)
                     
    def paint(self, painter: QPainter, option, widget=None):
        painter.setBrush(QBrush(self.hover_color if self.hovered else self.color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self.boundingRect())
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            event.accept()
        else:
            super().mousePressEvent(event)
            
    def hoverEnterEvent(self, event):
        self.hovered = True
        self.update()
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        self.hovered = False
        self.update()
        super().hoverLeaveEvent(event)
        
    def parent(self) -> Optional['WorkflowComponent']:
        return self._parent