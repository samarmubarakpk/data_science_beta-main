# src/frontend/ui/connection_line.py
from PyQt5.QtWidgets import QGraphicsPathItem
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPen, QPainterPath, QColor, QPainter
from PyQt5.QtGui import QLinearGradient

class ConnectionLine(QGraphicsPathItem):
    def __init__(self, start_port, end_port=None, parent=None):
        super().__init__(parent)
        self.start_port = start_port
        self.end_port = end_port
        self.setZValue(-1)  # Keep connections behind components
        
        # Visual styling
        self.pen = QPen(QColor("#94a3b8"), 2, Qt.SolidLine)
        self.pen.setCapStyle(Qt.RoundCap)
        self.setPen(self.pen)
        
    def updatePath(self, end_pos=None):
        """Update the connection line path."""
        if not self.start_port:
            return
            
        # Get start position
        start_pos = self.start_port.position
        if self.start_port.parent():
            start_pos = self.start_port.parent().pos() + start_pos
            
        # Get end position
        if end_pos is None and self.end_port:
            end_pos = self.end_port.position
            if self.end_port.parent():
                end_pos = self.end_port.parent().pos() + end_pos
            
        if end_pos:
            # Create curved path
            path = QPainterPath()
            path.moveTo(start_pos)
            
            # Calculate control points for curve
            dx = end_pos.x() - start_pos.x()
            control_x = dx * 0.5
            
            path.cubicTo(
                start_pos + QPointF(control_x, 0),  # First control point
                end_pos - QPointF(control_x, 0),    # Second control point
                end_pos                             # End point
            )
            
            self.setPath(path)
            
    def paint(self, painter, option, widget=None):
        """Paint the connection line with gradient effect."""
        if self.start_port and self.path():
            # Create gradient
            gradient = QLinearGradient(self.start_port.scenePos(), 
                                     self.end_port.scenePos() if self.end_port 
                                     else self.path().pointAtPercent(1))
            gradient.setColorAt(0, self.start_port.parent().color)
            if self.end_port:
                gradient.setColorAt(1, self.end_port.parent().color)
            
            # Set up pen with gradient
            pen = self.pen
            pen.setBrush(gradient)
            painter.setPen(pen)
            
            # Draw the path
            painter.drawPath(self.path())