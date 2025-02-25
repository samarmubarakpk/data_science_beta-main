# src/frontend/ui/canvas.py
from PyQt5.QtWidgets import (QGraphicsView, QGraphicsScene, QMenu, 
                           QGraphicsPathItem, QProgressDialog, QMessageBox , QGraphicsItem)
from PyQt5.QtCore import Qt, QPointF, QRectF, pyqtSignal, QMimeData
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QPainterPath, QLinearGradient
from typing import Dict, List, Optional, Set, Any
import logging
import json
from datetime import datetime
from pathlib import Path

from numpy import e

from src.frontend.components.cnn_component import CNNComponent
from src.frontend.components.file_component import FileComponent
from src.frontend.components.graph_component import GraphComponent
from src.backend.core.workflow_engine import WorkflowEngine
from src.frontend.components.base import WorkflowComponent, Port
from src.core.component_bridge import ComponentBridge
from src.frontend.utils.logger import get_logger

class ConnectionLine(QGraphicsPathItem):
    """Enhanced connection line with visual feedback and validation."""
    
    def __init__(self, start_port: Port, end_port: Optional[Port] = None, parent=None):
        super().__init__(parent)
        self.start_port = start_port
        self.end_port = end_port
        self.setZValue(-1)
        
        # Visual properties
        self.pen = QPen(QColor("#94a3b8"), 2, Qt.SolidLine)
        self.pen.setCapStyle(Qt.RoundCap)
        self.pen.setJoinStyle(Qt.RoundJoin)
        self.setPen(self.pen)
        
        # State colors
        self.default_color = QColor("#94a3b8")
        self.hover_color = QColor("#3b82f6")
        self.active_color = QColor("#4ade80")
        self.error_color = QColor("#ef4444")
        
        self.setAcceptHoverEvents(True)
        self.hovered = False

        self.start_port = start_port
        self.end_port = end_port
        self.setZValue(-1)
        
        # Make connection selectable
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        
        # Visual properties
        self.pen = QPen(QColor("#94a3b8"), 2, Qt.SolidLine)
        self.pen.setCapStyle(Qt.RoundCap)
        self.pen.setJoinStyle(Qt.RoundJoin)
        self.setPen(self.pen)
        
        # Colors for different states
        self.default_color = QColor("#94a3b8")
        self.hover_color = QColor("#3b82f6")
        self.selected_color = QColor("#60a5fa")

    def paint(self, painter: QPainter, option, widget=None):
        """Paint the connection with visual feedback for selection."""
        if self.isSelected():
            self.pen.setColor(self.selected_color)
            self.pen.setWidth(3)
        elif self.hovered:
            self.pen.setColor(self.hover_color)
            self.pen.setWidth(2)
        else:
            self.pen.setColor(self.default_color)
            self.pen.setWidth(2)
            
        painter.setPen(self.pen)
        painter.drawPath(self.path())

    def mousePressEvent(self, event):
        """Handle mouse press events for selection."""
        if event.button() == Qt.LeftButton:
            event.accept()
            self.setSelected(not self.isSelected())
        else:
            super().mousePressEvent(event)

    def execute_workflow(self):
        """Execute the workflow and update visualizations."""
        try:
            # Get ordered components
            ordered_components = self._get_execution_order()
            
            # Execute each component in order
            for component in ordered_components:
                # Get input data from connected components
                input_data = {}
                for conn in self.connections:
                    if conn.end_port.parent() == component:
                        source_component = conn.start_port.parent()
                        source_data = source_component.get_output()
                        input_data[conn.end_port.name] = source_data
                
                # Process component
                if isinstance(component, GraphComponent):
                    component.process_data(input_data.get("input"))
                else:
                    component.process(input_data)
                    
        except Exception as e:
            self.logger.error(f"Failed to execute workflow: {str(e)}")

    def update_position(self, end_point: Optional[QPointF] = None):
        """Update the connection line position with smooth curves."""
        if not self.start_port:
            return

        path = QPainterPath()
        start_pos = self.start_port.scenePos()
        end_pos = end_point if end_point else (self.end_port.scenePos() if self.end_port else start_pos)

        # Calculate smooth curve control points
        dx = end_pos.x() - start_pos.x()
        dy = end_pos.y() - start_pos.y()
        
        control_distance = min(abs(dx) * 0.5, 200)
        
        control1 = QPointF(start_pos.x() + control_distance, start_pos.y())
        control2 = QPointF(end_pos.x() - control_distance, end_pos.y())

        path.moveTo(start_pos)
        path.cubicTo(control1, control2, end_pos)
        self.setPath(path)

class WorkflowCanvas(QGraphicsView):
    """Enhanced canvas for workflow management with drag-and-drop support."""
    
    component_selected = pyqtSignal(WorkflowComponent)
    connection_created = pyqtSignal(object)
    status_message = pyqtSignal(str)
    modified_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.component_bridge = ComponentBridge()
        # Initialize core components
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.workflow_engine = WorkflowEngine()
        self.component_bridge = ComponentBridge()
        self._modified = False
        
        # Setup view properties
        self._setup_view_properties()
        self.setAcceptDrops(True)
        
        # Initialize state variables
        self._initialize_state()
        
        # Setup undo/redo system
        self._setup_undo_redo()
        self.current_connection = None

        
        # Draw grid
        self._draw_grid()
        self.undo_stack = []
        self.redo_stack = []
        self.max_undo_steps = 50
        self._modified = False

    @property
    def modified(self) -> bool:
        """Get modification state."""
        return self._modified

    @modified.setter
    def modified(self, value: bool):
        """Set modification state and emit signal if changed."""
        if self._modified != value:
            self._modified = value
            self.modified_changed.emit(value)


    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        if event.key() == Qt.Key_Delete:
            self.delete_selected_items()
        else:
            super().keyPressEvent(event)


    def add_connection(self, connection):
        """Add a connection and trigger data flow."""
        print("Canvas: Adding connection...")
        self.connections.add(connection)
        source_comp = connection.start_port.parent()
        target_comp = connection.end_port.parent()
        
        try:
            if isinstance(source_comp, CNNComponent) and isinstance(target_comp, GraphComponent):
                print("Canvas: CNN -> Graph connection detected")
                if hasattr(source_comp, '_metrics'):
                    print("Canvas: Passing metrics and predictions to graph component")
                    target_comp.execute({
                        "input": {
                            "metrics": source_comp._metrics,
                            "predictions": getattr(source_comp, '_predictions', None),
                            "true_labels": getattr(source_comp, '_true_labels', None),
                            "status": "success"
                        }
                    })
                else:
                    print("Canvas: No metrics available yet – CNN component needs to be trained first")
            else:
                print(f"Canvas: Generic connection between {type(source_comp).__name__} and {type(target_comp).__name__}")
                # Generic data flow
                result = source_comp.execute(inputs={})
                if result and result.get("status") == "success":
                    target_comp.execute({"input": result.get("output")})

        except Exception as e:
            print(f"Canvas ERROR in add_connection: {str(e)}")

        self.update()

     
    def delete_selected_items(self):
        """Delete all selected items from the canvas."""
        selected_items = self.scene.selectedItems()
        if not selected_items:
            return
            
        self.push_undo_state()
        
        for item in selected_items:
            if isinstance(item, WorkflowComponent):
                self.remove_component(item)
            elif isinstance(item, ConnectionLine):
                self.remove_connection(item)

    def remove_component(self, component):
        """Remove a component and all its connections."""
        if component.id not in self.components:
            return

        # Find and remove all connections to/from this component
        connections_to_remove = {
            conn for conn in self.connections 
            if conn.start_port.parent() == component or 
               conn.end_port.parent() == component
        }
        
        for conn in connections_to_remove:
            self.remove_connection(conn)
            
        # Remove the component
        self.scene.removeItem(component)
        del self.components[component.id]
        self.modified = True
        self.status_message.emit(f"Removed {component.title}")

    def remove_connection(self, connection):
        """Remove a connection between components."""
        if connection in self.connections:
            self.connections.remove(connection)
            self.scene.removeItem(connection)
            self.modified = True
            self.status_message.emit("Connection removed")

    def contextMenuEvent(self, event):
        """Show context menu for components and connections."""
        item = self.itemAt(event.pos())
        menu = QMenu(self)
        
        if isinstance(item, WorkflowComponent):
            delete_action = menu.addAction("Delete Component")
            delete_action.triggered.connect(lambda: self.remove_component(item))
            
        elif isinstance(item, ConnectionLine):
            delete_action = menu.addAction("Delete Connection")
            delete_action.triggered.connect(lambda: self.remove_connection(item))
            
        if not menu.isEmpty():
            menu.exec_(event.globalPos())


    def update_connections(self):
        """Update all connection positions when components move."""
        try:
            for connection in self.connections:
                connection.update_position()
        except Exception as e:
            self.logger.error(f"Failed to update connections: {str(e)}")

    def start_connection(self, port):
        """Start drawing a connection from a port."""
        try:
            self.current_connection = ConnectionLine(port)
            self.scene.addItem(self.current_connection)
        except Exception as e:
            self.logger.error(f"Failed to start connection: {str(e)}")

    def update_current_connection(self, pos):
        """Update the current connection line while dragging."""
        if self.current_connection:
            self.current_connection.update_position(self.mapToScene(pos))

    def finish_connection(self, end_port):
        """Complete a connection to an end port."""
        if self.current_connection:
            print("Canvas: Completing connection")
            self.current_connection.end_port = end_port
            self.current_connection.update_position()
            self.add_connection(self.current_connection)
            self.current_connection = None

    def can_connect(self, port1, port2):
        """Check if two ports can be connected."""
        try:
            # Don't connect ports of same type (input-input or output-output)
            if port1.is_output == port2.is_output:
                return False
                
            # Make sure ports are from different components
            parent1 = port1.parent()
            parent2 = port2.parent()
            if parent1 is None or parent2 is None or parent1 == parent2:
                return False
                
            # Check for existing connections to input port
            input_port = port2 if not port2.is_output else port1
            if any(conn.end_port == input_port for conn in self.connections):
                return False
                
            # Validate port types match
            port_types_match = (port1.port_type == port2.port_type or 
                              port1.port_type == "any" or 
                              port2.port_type == "any")
            return port_types_match
            
        except Exception as e:
            self.logger.error(f"Connection validation failed: {str(e)}")
            return False

    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        if self.current_connection:
            self.update_current_connection(event.pos())
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        if event.button() == Qt.LeftButton and self.current_connection:
            item = self.itemAt(event.pos())
            if isinstance(item, Port):
                if self.finish_connection(item):
                    self.connection_created.emit(self.current_connection)
            else:
                self.scene.removeItem(self.current_connection)
                self.current_connection = None
        
        super().mouseReleaseEvent(event)
    
    def push_undo_state(self):
        """Push current state to undo stack."""
        try:
            state = self.save_state()
            if len(self.undo_stack) >= self.max_undo_steps:
                self.undo_stack.pop(0)
                self.undo_stack.append(state)
                self.redo_stack.clear()
                self.modified = True
        except Exception as e:
            self.logger.error(f"Failed to push undo state: {str(e)}")

    def save_state(self) -> dict:
        """Save current state of the canvas."""
        state = {
            'components': {},
            'connections': []
        }
        
        # Save components
        for id, comp in self.components.items():
            state['components'][id] = {
                'type': comp.__class__.__name__,
                'position': {'x': comp.pos().x(), 'y': comp.pos().y()},
                'properties': comp.properties.copy() if hasattr(comp, 'properties') else {}
            }
        
        # Save connections
        for conn in self.connections:
            if conn.end_port:  # Only save complete connections
                state['connections'].append({
                    'start_port': {
                        'component': conn.start_port.parent().id,
                        'port_name': conn.start_port.name
                    },
                    'end_port': {
                        'component': conn.end_port.parent().id,
                        'port_name': conn.end_port.name
                    }
                })
        
        return state

    def restore_state(self, state: dict):
        """Restore canvas to a saved state."""
        try:
            # Clear current state
            self.clear(save_state=False)
            
            # Restore components
            for comp_id, comp_data in state['components'].items():
                component = self.create_component({'type': comp_data['type']})
                if component:
                    component.setPos(comp_data['position']['x'], 
                                  comp_data['position']['y'])
                    if hasattr(component, 'properties'):
                        component.properties = comp_data['properties'].copy()
                    self.add_component(component, save_state=False)
            
            # Restore connections
            for conn_data in state['connections']:
                self.restore_connection(conn_data)
                
        except Exception as e:
            self.logger.error(f"Failed to restore state: {str(e)}")

    def restore_connection(self, conn_data: dict):
        """Restore a connection from saved data."""
        try:
            # Find components
            start_comp = self.components.get(conn_data['start_port']['component'])
            end_comp = self.components.get(conn_data['end_port']['component'])
            
            if not (start_comp and end_comp):
                return
            
            # Find ports
            start_port = next((p for p in start_comp.output_ports.values() 
                             if p.name == conn_data['start_port']['port_name']), None)
            end_port = next((p for p in end_comp.input_ports.values() 
                           if p.name == conn_data['end_port']['port_name']), None)
            
            if not (start_port and end_port):
                return
            
            # Create connection
            connection = ConnectionLine(start_port, end_port)
            self.scene.addItem(connection)
            self.connections.add(connection)
            connection.update_position()
            
        except Exception as e:
            self.logger.error(f"Failed to restore connection: {str(e)}")

    def undo(self):
        """Perform undo operation."""
        if not self.undo_stack:
            return
            
        try:
            current_state = self.save_state()
            self.redo_stack.append(current_state)
            state = self.undo_stack.pop()
            self.restore_state(state)
            self.status_message.emit("Undo")
        except Exception as e:
            self.logger.error(f"Undo failed: {str(e)}")

    def redo(self):
        """Perform redo operation."""
        if not self.redo_stack:
            return
            
        try:
            current_state = self.save_state()
            self.undo_stack.append(current_state)
            state = self.redo_stack.pop()
            self.restore_state(state)
            self.status_message.emit("Redo")
        except Exception as e:
            self.logger.error(f"Redo failed: {str(e)}")

    def clear(self, save_state: bool = True):
        """Clear the canvas."""
        if save_state:
            self.push_undo_state()
            
        for item in self.scene.items():
            self.scene.removeItem(item)
            
        self.components.clear()
        self.connections.clear()
        self.current_connection = None
        self.modified = False
        self.status_message.emit("Canvas cleared")

    def is_modified(self) -> bool:
        """Method to check if canvas is modified (for compatibility)."""
        return self.modified

    def dragEnterEvent(self, event):
        """Handle drag enter events."""
        self.logger.debug("Drag enter event received")
        if event.mimeData().hasText():
            try:
                # Try to parse component data
                component_data = json.loads(event.mimeData().text())
                if "type" in component_data:
                    event.acceptProposedAction()
                    self.logger.debug("Drag enter accepted")
                    return
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse drag data: {str(e)}")
                
        # Handle workflow files
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().endswith('.workflow'):
                    event.acceptProposedAction()
                    return

    def dragMoveEvent(self, event):
        """Handle drag move events."""
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """Handle drop events."""
        try:
            self.logger.debug("Drop event received")
            if event.mimeData().hasText():
                # Get the drop position in scene coordinates
                pos = self.mapToScene(event.pos())
                
                # Parse component data
                component_data = json.loads(event.mimeData().text())
                self.logger.debug(f"Dropped component data: {component_data}")
                
                # Create the component
                component = self.create_component(component_data)
                if component:
                    # Position the component
                    component.setPos(pos.x() - component.boundingRect().width()/2,
                                  pos.y() - component.boundingRect().height()/2)
                    
                    # Add to canvas
                    self.add_component(component)
                    event.acceptProposedAction()
                    self.logger.debug(f"Component {component.title} added successfully")
                    return
                    
        except Exception as e:
            self.logger.error(f"Drop event failed: {str(e)}")

    def create_component(self, data: dict) -> Optional[WorkflowComponent]:
        """Create a new component from drop data."""
        try:
            self.logger.debug(f"Creating component from data: {data}")
            component_type = data.get("type")
            
            # Import and create appropriate component
            if component_type == "FileComponent":
                from src.frontend.components.file_component import FileComponent
                return FileComponent()
            elif component_type == "GraphComponent":
                from src.frontend.components.graph_component import GraphComponent
                return GraphComponent()
            elif component_type == "CNNComponent":
                from src.frontend.components.cnn_component import CNNComponent
                return CNNComponent()
            else:
                self.logger.error(f"Unknown component type: {component_type}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to create component: {str(e)}")
            return None

    def add_component(self, component: WorkflowComponent, save_state: bool = True) -> None:
        """Add a component to the canvas."""
        try:
            if save_state:
                self.push_undo_state()
                
            self.scene.addItem(component)
            self.components[component.id] = component
            
            # Connect signals
            if hasattr(component, 'position_changed'):
                component.position_changed.connect(self.update_connections)
            
            self.modified = True
            self.status_message.emit(f"Added {component.title}")
            
        except Exception as e:
            self.logger.error(f"Failed to add component: {str(e)}")

    def _setup_view_properties(self):
        """Configure view properties for optimal rendering."""
        self.setRenderHint(QPainter.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setAcceptDrops(True)
        
    def _initialize_state(self):
        """Initialize canvas state variables."""
        self.components: Dict[str, WorkflowComponent] = {}
        self.connections: Set[ConnectionLine] = set()
        self.current_connection: Optional[ConnectionLine] = None
        self.is_panning = False
        self.last_mouse_pos = None
        self._modified = False
        
    def _setup_undo_redo(self):
        """Initialize undo/redo system."""
        self.undo_stack = []
        self.redo_stack = []
        self.max_undo_steps = 50

    def dragEnterEvent(self, event):
        """Handle component drag enter events."""
        if event.mimeData().hasText():
            try:
                data = json.loads(event.mimeData().text())
                if "type" in data:
                    event.acceptProposedAction()
                    return
            except json.JSONDecodeError:
                pass
            
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().endswith('.workflow'):
                    event.acceptProposedAction()
                    return

    def dropEvent(self, event):
        """Handle component drop events with position snapping."""
        try:
            if event.mimeData().hasText():
                pos = self.mapToScene(event.pos())
                
                # Snap to grid
                grid_size = 20
                pos.setX(round(pos.x() / grid_size) * grid_size)
                pos.setY(round(pos.y() / grid_size) * grid_size)
                
                component_data = json.loads(event.mimeData().text())
                component = self.create_component(component_data)
                
                if component:
                    component.setPos(pos)
                    self.add_component(component)
                    event.acceptProposedAction()
                    
        except Exception as e:
            self.logger.error(f"Drop event failed: {str(e)}")

    def mousePressEvent(self, event):
        """Handle mouse press events for component selection and connection creation."""
        if event.button() == Qt.LeftButton:
            item = self.itemAt(event.pos())
            
            if isinstance(item, Port):
                self.start_connection(item)
            elif isinstance(item, WorkflowComponent):
                self.component_selected.emit(item)
            elif isinstance(item, ConnectionLine):
                item.setSelected(True)
            
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move events for connection drawing and panning."""
        if self.current_connection:
            self.current_connection.update_position(self.mapToScene(event.pos()))
        elif self.is_panning and self.last_mouse_pos:
            delta = event.pos() - self.last_mouse_pos
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y())
            self.last_mouse_pos = event.pos()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events for completing connections."""
        if event.button() == Qt.LeftButton and self.current_connection:
            item = self.itemAt(event.pos())
            if isinstance(item, Port):
                if self.finish_connection(item):
                    self.connection_created.emit(self.current_connection)
            else:
                self.scene.removeItem(self.current_connection)
                self.current_connection = None
                
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        if event.key() == Qt.Key_Delete:
            for item in self.scene.selectedItems():
                if isinstance(item, WorkflowComponent):
                    self.remove_component(item)
                elif isinstance(item, ConnectionLine):
                    self.remove_connection(item)
        elif event.key() == Qt.Key_Space:
            self.toggle_pan_mode()
        elif event.modifiers() & Qt.ControlModifier:
            if event.key() == Qt.Key_Z:
                if event.modifiers() & Qt.ShiftModifier:
                    self.redo()
                else:
                    self.undo()
            elif event.key() == Qt.Key_Y:
                self.redo()
                
        super().keyPressEvent(event)

    # ... [Previous methods remain unchanged] ...

    def validate_workflow(self) -> List[str]:
        """Validate the entire workflow before execution."""
        issues = []
        
        # Validate components
        for component in self.components.values():
            # Check required inputs
            for port_name in component.get_required_inputs():
                if not any(conn.end_port.parent() == component and 
                          conn.end_port.name == port_name 
                          for conn in self.connections):
                    issues.append(f"{component.title}: Required input '{port_name}' not connected")
        
        # Check for cycles
        if self._has_cycles():
            issues.append("Workflow contains cycles")
        
        return issues

    def _has_cycles(self) -> bool:
        """Check for cycles in the workflow using DFS."""
        visited = set()
        path = set()
        
        def visit(component):
            if component in path:
                return True
            if component in visited:
                return False
            
            visited.add(component)
            path.add(component)
            
            for conn in self.connections:
                if conn.start_port.parent() == component:
                    if visit(conn.end_port.parent()):
                        return True
            
            path.remove(component)
            return False
        
        return any(visit(comp) for comp in self.components.values())

    def execute_workflow(self) -> Dict[str, Any]:
        """Execute the workflow with progress tracking."""
        progress = QProgressDialog("Executing workflow...", "Cancel", 0, len(self.components), self)
        progress.setWindowModality(Qt.WindowModal)
        
        try:
            # Validate workflow
            issues = self.validate_workflow()
            if issues:
                issues_text = "\n".join(f"- {issue}" for issue in issues)
                QMessageBox.warning(self, "Validation Issues", 
                                  f"Cannot execute workflow:\n\n{issues_text}")
                return {}
            
            # Execute components in order
            ordered_components = self._get_execution_order()
            results = {}
            
            for i, component in enumerate(ordered_components):
                if progress.wasCanceled():
                    break
                    
                progress.setValue(i)
                progress.setLabelText(f"Executing {component.title}...")
                
                # Execute component
                component_results = self._execute_component(component)
                if component_results.get("status") == "error":
                    raise RuntimeError(f"Component {component.title} failed: {component_results.get('error')}")
                    
                results[component.id] = component_results
                
            return results
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {str(e)}")
            QMessageBox.critical(self, "Execution Error", 
                               f"Workflow execution failed:\n{str(e)}")
            return {}
            
        finally:
            progress.close()

    def _get_execution_order(self) -> List[WorkflowComponent]:
        """
        Determine the correct execution order of components using topological sort.
        Returns a list of components in execution order.
        Raises RuntimeError if a cycle is detected.
        """
        # Initialize data structures
        in_degree = {comp: 0 for comp in self.components.values()}
        graph = {comp: set() for comp in self.components.values()}
        
        # Build the graph and calculate in-degrees
        for connection in self.connections:
            source = connection.start_port.parent()
            target = connection.end_port.parent()
            graph[source].add(target)
            in_degree[target] += 1
        
        # Initialize queue with nodes that have no dependencies
        queue = [comp for comp, degree in in_degree.items() if degree == 0]
        if not queue:
            raise RuntimeError("Circular dependency detected: no valid starting point found")
        
        # Process the queue
        execution_order = []
        while queue:
            # Take the next component from queue
            current = queue.pop(0)
            execution_order.append(current)
            
            # Process all components that depend on current
            for dependent in graph[current]:
                in_degree[dependent] -= 1
                # If all dependencies are satisfied, add to queue
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        # Check for cycles
        if len(execution_order) != len(self.components):
            raise RuntimeError("Circular dependency detected: not all components can be ordered")
            
        self.logger.debug(f"Execution order determined: {[comp.title for comp in execution_order]}")
        return execution_order

    def _execute_component(self, component: WorkflowComponent) -> Dict[str, Any]:
        """Execute a single component with error handling."""
        try:
            # Get input data from connected components
            inputs = self._get_component_inputs(component)
            
            # Execute component
            return component.execute(inputs)
            
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _get_component_inputs(self, component: WorkflowComponent) -> Dict[str, Any]:
        """Get input data for a component from its connections."""
        inputs = {}
        for conn in self.connections:
            if conn.end_port.parent() == component:
                source_component = conn.start_port.parent()
                source_port = conn.start_port.name
                target_port = conn.end_port.name
                
                # Get output from source component
                source_outputs = source_component.get_outputs()
                if source_port in source_outputs:
                    inputs[target_port] = source_outputs[source_port]
                    
        return inputs

    def _draw_grid(self):
        """Draw background grid for visual guidance."""
        grid_size = 20
        grid_color = QColor("#f0f0f0")
        
        for x in range(0, int(self.scene.width()), grid_size):
            self.scene.addLine(x, 0, x, self.scene.height(), QPen(grid_color))
            
        for y in range(0, int(self.scene.height()), grid_size):
            self.scene.addLine(0, y, self.scene.width(), y, QPen(grid_color))

    
    def save_to_file(self, filename: str) -> bool:
        """Save the workflow state to a file."""
        try:
            workflow_state = {
                'components': {},
                'connections': []
            }
            
            # Save components
            for comp_id, component in self.components.items():
                workflow_state['components'][comp_id] = {
                    'type': component.__class__.__name__,
                    'position': {
                        'x': component.pos().x(),
                        'y': component.pos().y()
                    },
                    'properties': component.get_properties()
                }
            
            # Save connections
            for connection in self.connections:
                workflow_state['connections'].append({
                    'start': {
                        'component': connection.start_port.parent().id,
                        'port': connection.start_port.name
                    },
                    'end': {
                        'component': connection.end_port.parent().id,
                        'port': connection.end_port.name
                    }
                })
            
            # Save to file
            with open(filename, 'w') as f:
                json.dump(workflow_state, f, indent=2)
                
            self.modified = False
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save workflow: {str(e)}")
            return False