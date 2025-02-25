# src/frontend/components/base.py
from PyQt5.QtWidgets import QGraphicsObject, QGraphicsItem
from PyQt5.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QPainterPath
from typing import Dict, Any, List, Optional
import uuid

class Port(QGraphicsItem):
    """Represents an input/output port on a component."""
    def __init__(self, name: str, port_type: str, position: QPointF, is_output: bool = False, parent=None):
        super().__init__(parent)
        self.name = name
        self.port_type = port_type
        self.is_output = is_output
        self.setPos(position)
        self.radius = 4
        self.color = QColor("#4ade80") if is_output else QColor("#60a5fa")
        self._parent_component = parent  # Store the parent component
        self.port_type = port_type
        self.position = position
        self.is_output = is_output
        self.parent_component = None
        self.color = QColor("#4CAF50") if is_output else QColor("#2196F3")
        
        # Make port interactive
        self.setAcceptHoverEvents(True)



    def scenePos(self):
        """Get the port's position in scene coordinates."""
        if self.parent_component:
            return self.parent_component.pos() + self.position
        return self.position


    def parent(self):
        """Get the parent component."""
        return self.parent_component

    def scenePos(self):
        """Get the port's position in scene coordinates."""
        if self.parent_component:
            return self.parent_component.pos() + self.position
        return self.position
        
    def boundingRect(self) -> QRectF:
        """Define the clickable area of the port."""
        return QRectF(-self.radius, -self.radius,
                     self.radius * 2, self.radius * 2)
                     
    def paint(self, painter: QPainter, option, widget=None):
        """Draw the port."""
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(self.color))
        painter.drawEllipse(self.boundingRect())
        
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if hasattr(self.scene(), 'start_connection'):
            self.scene().start_connection(self)
        event.accept()
        
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        if hasattr(self.scene(), 'finish_connection'):
            self.scene().finish_connection(self)
        event.accept()

    def hoverEnterEvent(self, event):
        """Handle hover enter events."""
        self.color = QColor("#3b82f6")  # Highlight color
        self.update()
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        """Handle hover leave events."""
        self.color = QColor("#4ade80") if self.is_output else QColor("#60a5fa")
        self.update()
        super().hoverLeaveEvent(event)
        
    def parent(self) -> Optional['WorkflowComponent']:
        """Get the parent component of this port."""
        return self._parent_component
        
    def scenePos(self) -> QPointF:
        """Get the port's position in scene coordinates."""
        return self.mapToScene(QPointF(0, 0))
        
    def get_state(self) -> Dict[str, Any]:
        """Get port state for saving."""
        return {
            "name": self.name,
            "type": self.port_type,
            "position": {"x": self.pos().x(), "y": self.pos().y()},
            "is_output": self.is_output
        }

class WorkflowComponent(QGraphicsObject):
    """Base class for all workflow components."""
    
    position_changed = pyqtSignal()
    property_changed = pyqtSignal(str, dict)  # Added for property changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.id = str(uuid.uuid4())
        self.title = "Base Component"
        self.width = 100  # Reduced size
        self.height = 60  # Reduced size
        # self.id = str(uuid.uuid4())
        # self.title = "Base Component"
        # self.width = 120  # Reduced from 150
        # self.height = 80
        
        # Colors
        self.color = QColor("#2563eb")
        self.selected_color = QColor("#1e40af")
        self.hover_color = QColor("#3b82f6")
        
        # Component properties
        self.input_ports: Dict[str, Port] = {}
        self.output_ports: Dict[str, Port] = {}
        self.properties: Dict[str, Any] = {}
        
        # Set flags
        self.setFlag(QGraphicsObject.ItemIsMovable)
        self.setFlag(QGraphicsObject.ItemIsSelectable)
        self.setFlag(QGraphicsObject.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        
        # Hover state
        self.hovered = False
        
    def boundingRect(self) -> QRectF:
        """Define the bounding rectangle of the component."""
        return QRectF(0, 0, self.width, self.height)
        
    def paint(self, painter: QPainter, option, widget=None):
        """Paint the component with enhanced visuals."""
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw shadow
        path = QPainterPath()
        path.addRoundedRect(self.boundingRect().adjusted(2, 2, 2, 2), 8, 8)
        painter.fillPath(path, QColor(0, 0, 0, 30))
        
        # Draw component body
        path = QPainterPath()
        path.addRoundedRect(self.boundingRect(), 8, 8)
        
        # Set color based on state
        if self.isSelected():
            color = self.selected_color
        elif self.hovered:
            color = self.hover_color
        else:
            color = self.color
            
        pen = QPen(color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.fillPath(path, QBrush(QColor("#ffffff")))
        painter.drawPath(path)
        
        # Draw title
        painter.setPen(QPen(QColor("#1e293b")))
        painter.drawText(self.boundingRect().adjusted(8, 4, -8, -4), 
                        Qt.AlignTop | Qt.AlignHCenter, 
                        self.title)
                        
    def add_input_port(self, name: str, port_type: str, y_position: float):
        """Add an input port to the component."""
        port = Port(name, port_type, QPointF(0, y_position), False, self)
        self.input_ports[name] = port
        
    def add_output_port(self, name: str, port_type: str, y_position: float):
        """Add an output port to the component."""
        port = Port(name, port_type, QPointF(self.width, y_position), True, self)
        self.output_ports[name] = port
        
    def get_properties(self) -> Dict[str, Any]:
        """Get component properties for the property editor."""
        return self.properties
        
    def set_property(self, name: str, value: Any):
        """Set a component property and emit change signal."""
        if name in self.properties:
            if isinstance(self.properties[name]["value"], dict):
                self.properties[name]["value"]["selected"] = value
            else:
                self.properties[name]["value"] = value
            self.property_changed.emit(self.id, {name: value})
            self.update()
            
    def get_state(self) -> Dict[str, Any]:
        """Get component state for saving."""
        return {
            "id": self.id,
            "type": self.__class__.__name__,
            "position": {"x": self.pos().x(), "y": self.pos().y()},
            "properties": self.properties
        }
        
    def load_state(self, state: Dict[str, Any]):
        """Load component state."""
        self.id = state["id"]
        self.setPos(state["position"]["x"], state["position"]["y"])
        self.properties = state["properties"].copy()
        self.update()
        
    def validate_connection(self, other: 'WorkflowComponent', my_port: str, other_port: str) -> bool:
        """Validate connection compatibility between components.
        
        Args:
            other: The other component to connect to
            my_port: Name of the port on this component
            other_port: Name of the port on the other component
            
        Returns:
            bool: True if connection is valid, False otherwise
        """
        # Get port objects
        my_port_obj = self.output_ports.get(my_port) or self.input_ports.get(my_port)
        other_port_obj = other.output_ports.get(other_port) or other.input_ports.get(other_port)
        
        if not (my_port_obj and other_port_obj):
            return False
            
        # Don't connect inputs to inputs or outputs to outputs
        if my_port_obj.is_output == other_port_obj.is_output:
            return False
            
        # Don't connect a component to itself
        if self == other:
            return False
            
        # Check data type compatibility
        return (my_port_obj.port_type == other_port_obj.port_type or 
                my_port_obj.port_type == "any" or 
                other_port_obj.port_type == "any")
        
    def itemChange(self, change, value):
        """Handle item changes and emit signals."""
        if change == QGraphicsObject.ItemPositionChange:
            self.position_changed.emit()
        elif change == QGraphicsObject.ItemSelectedChange:
            if value and hasattr(self.scene(), 'component_selected'):
                self.scene().component_selected.emit(self)
        return super().itemChange(change, value)

    def get_required_inputs(self) -> List[str]:
        """Get list of required input ports."""
        return list(self.input_ports.keys())
    
    def add_input_port(self, name: str, port_type: str, y_position: float):
        """Add an input port to the component."""
        # Create the port at the left side of the component
        position = QPointF(0.0, float(y_position))  # Ensure float values
        port = Port(name, port_type, position, False, self)
        self.input_ports[name] = port
        
    def add_output_port(self, name: str, port_type: str, y_position: float):
        """Add an output port to the component."""
        # Create the port at the right side of the component
        position = QPointF(float(self.width), float(y_position))  # Ensure float values
        port = Port(name, port_type, position, True, self)
        self.output_ports[name] = port