# src/frontend/ui/component_palette.py
from PyQt5.QtWidgets import (QDockWidget, QWidget, QVBoxLayout, QScrollArea,
                           QLabel, QToolButton, QGridLayout, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal, QMimeData, QSize, QPoint
from PyQt5.QtGui import QIcon, QDrag, QPixmap, QPainter, QColor, QBrush, QPen
import json
from typing import Optional, Dict, Type
import os


from src.backend.utils.loggers import get_logger
from src.frontend.components.file_component import FileComponent
from src.frontend.components.graph_component import GraphComponent
from src.frontend.components.cnn_component import CNNComponent
from src.frontend.components.base import WorkflowComponent

class ComponentButton(QToolButton):
    def __init__(self, title: str, component_class, icon_path: str = None, parent=None):
        super().__init__(parent)
        self.title = title
        self.component_class = component_class
        self.logger = get_logger(__name__)
        
        # Setup button appearance
        self.setText(title)
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.setIconSize(QSize(32, 32))
        
        # Set icon directly here instead of separate method
        if icon_path and os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
        else:
            # Default icons based on type
            if "File" in title:
                self.setIcon(QIcon(":/icons/file.png"))
            elif "Graph" in title:
                self.setIcon(QIcon(":/icons/graph.png"))
            elif "CNN" in title:
                self.setIcon(QIcon(":/icons/cnn.png"))
            else:
                self.setIcon(QIcon(":/icons/component.png"))
        
        # Setup style
        self.setFixedSize(80, 80)
        self.setStyleSheet("""
            QToolButton {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                background-color: white;
                font-size: 11px;
                padding: 4px;
            }
            QToolButton:hover {
                background-color: #f0f9ff;
                border-color: #60a5fa;
            }
            QToolButton:pressed {
                background-color: #e0f2fe;
                border-color: #3b82f6;
            }
        """)
        
    def _setup_icon(self, icon_path: str):  # Remove title parameter
        """Setup the component icon."""
        if icon_path and os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
        else:
            # Default icons based on component type
            icon_map = {
                "File": ":/icons/file.png",
                "Graph": ":/icons/graph.png",
                "CNN": ":/icons/cnn.png",
                "Data": ":/icons/data.png",
                "Process": ":/icons/process.png",
                "Visualize": ":/icons/visualize.png"
            }
            
            # Find matching icon based on the button's title
            for key, path in icon_map.items():
                if key in self.title:  # Use self.title instead of title parameter
                    self.setIcon(QIcon(path))
                    break
            else:
                # Default icon if no match found
                self.setIcon(QIcon(":/icons/component.png"))
    
    def _setup_style(self):
        """Setup the button's visual style."""
        self.setFixedSize(80, 80)
        self.setStyleSheet("""
            QToolButton {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                background-color: white;
                font-size: 11px;
                padding: 4px;
            }
            QToolButton:hover {
                background-color: #f0f9ff;
                border-color: #60a5fa;
            }
            QToolButton:pressed {
                background-color: #e0f2fe;
                border-color: #3b82f6;
            }
        """)

    def mousePressEvent(self, event):
        """Handle mouse press event to start drag operation."""
        if event.button() == Qt.LeftButton:
            try:
                drag = QDrag(self)
                mime_data = QMimeData()
                
                # Create component data
                component_data = {
                    "type": self.component_class.__name__,
                    "title": self.title
                }
                mime_data.setText(json.dumps(component_data))
                drag.setMimeData(mime_data)
                
                # Create drag pixmap
                pixmap = QPixmap(self.size())
                pixmap.fill(Qt.transparent)
                painter = QPainter(pixmap)
                self.render(painter)
                painter.end()
                
                # Set drag hot spot to center
                drag.setPixmap(pixmap)
                drag.setHotSpot(QPoint(pixmap.width()//2, pixmap.height()//2))
                
                # Execute drag
                result = drag.exec_(Qt.CopyAction)
                self.logger.debug(f"Drag operation completed with result: {result}")
                
            except Exception as e:
                self.logger.error(f"Failed to start drag operation: {str(e)}")

        
    def _setup_icon(self, icon_path: str, title: str):
        """Setup the component icon."""
        if icon_path and os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
        else:
            # Default icons based on component type
            icon_map = {
                "File": ":/icons/file.png",
                "Graph": ":/icons/graph.png",
                "CNN": ":/icons/cnn.png",
                "Data": ":/icons/data.png",
                "Process": ":/icons/process.png",
                "Visualize": ":/icons/visualize.png"
            }
            
            # Find matching icon
            for key, path in icon_map.items():
                if key in title:
                    self.setIcon(QIcon(path))
                    break
            else:
                # Default icon if no match found
                self.setIcon(QIcon(":/icons/component.png"))
    
    # In ComponentButton class, modify _setup_style method
    def _setup_style(self):
        """Setup the button's visual style."""
        self.setFixedSize(80, 80)
        self.setStyleSheet("""
            QToolButton {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                background-color: white;
                font-size: 11px;
                padding: 4px;
            }
            QToolButton:hover {
                background-color: #f0f9ff;
                border-color: #60a5fa;
            }
            QToolButton:pressed {
                background-color: #e0f2fe;
                border-color: #3b82f6;
            }
        """)
    
    def mousePressEvent(self, event):
        """Handle mouse press event to start drag operation."""
        if event.button() == Qt.LeftButton:
            try:
                self.is_dragging = True
                
                # Create drag object
                drag = QDrag(self)
                
                # Prepare mime data
                mime_data = QMimeData()
                component_data = {
                    "type": self.component_class.__name__,
                    "title": self.title
                }
                mime_data.setText(json.dumps(component_data))
                drag.setMimeData(mime_data)
                
                # Create drag feedback pixmap
                pixmap = self._create_drag_pixmap()
                drag.setPixmap(pixmap)
                drag.setHotSpot(QPoint(pixmap.width() // 2, pixmap.height() // 2))
                
                # Execute drag operation
                drag_result = drag.exec_(Qt.CopyAction)
                self.logger.debug(f"Drag operation completed with result: {drag_result}")
                
            except Exception as e:
                self.logger.error(f"Failed to start drag operation: {str(e)}")
            finally:
                self.is_dragging = False
                
    def _create_drag_pixmap(self) -> QPixmap:
        """Create an enhanced pixmap for drag feedback."""
        # Create base pixmap
        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw component preview
        rect = pixmap.rect().adjusted(4, 4, -4, -4)
        
        # Draw shadow
        shadow_color = QColor(0, 0, 0, 30)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(shadow_color))
        painter.drawRoundedRect(rect.adjusted(2, 2, 2, 2), 8, 8)
        
        # Draw background
        painter.setBrush(QBrush(QColor("white")))
        painter.setPen(QPen(QColor("#60a5fa"), 2))
        painter.drawRoundedRect(rect, 8, 8)
        
        # Draw icon and text
        if not self.icon().isNull():
            icon_rect = rect.adjusted(8, 4, -8, -24)
            self.icon().paint(painter, icon_rect, Qt.AlignCenter)
        
        painter.setPen(QPen(QColor("#1e293b")))
        painter.drawText(rect, Qt.AlignBottom | Qt.AlignHCenter, self.title)
        
        painter.end()
        return pixmap

class CategoryWidget(QFrame):
    """Enhanced category widget with better visual organization."""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.logger = get_logger(__name__)
        
        # Setup layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(8)
        
        # Create header
        self._setup_header(title)
        
        # Setup grid for components
        self.grid = QGridLayout()
        self.grid.setSpacing(8)
        self.layout.addLayout(self.grid)
        
        # Initialize grid position tracking
        self.current_row = 0
        self.current_col = 0
        self.max_cols = 3
        
        # Apply styling
        self.setStyleSheet("""
            CategoryWidget {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                margin: 4px;
            }
        """)
        
    def _setup_header(self, title: str):
        """Setup the category header."""
        header = QLabel(title)
        header.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: bold;
                color: #334155;
                padding: 8px;
                background: #f8fafc;
                border-radius: 4px;
                border: 1px solid #e2e8f0;
            }
        """)
        self.layout.addWidget(header)
    
    def add_component(self, component_button: ComponentButton):
        """Add a component button to the grid layout."""
        try:
            self.grid.addWidget(component_button, 
                              self.current_row, 
                              self.current_col)
            
            self.current_col += 1
            if self.current_col >= self.max_cols:
                self.current_col = 0
                self.current_row += 1
                
        except Exception as e:
            self.logger.error(f"Failed to add component button: {str(e)}")

class ComponentPalette(QDockWidget):
    """Enhanced component palette with improved organization and error handling."""
    
    component_created = pyqtSignal(WorkflowComponent)
    
    def __init__(self, parent=None):
        super().__init__("Components", parent)
        self.logger = get_logger(__name__)
        
        # Store registered components
        self.component_registry: Dict[str, Type[WorkflowComponent]] = {
            'FileComponent': FileComponent,
            'GraphComponent': GraphComponent,
            'CNNComponent': CNNComponent
        }
        
        self.setup_ui()
        self.register_components()
    
    def setup_ui(self):
        """Setup the palette's user interface."""
        # Create main widget and layout
        self.main_widget = QWidget()
        self.layout = QVBoxLayout(self.main_widget)
        self.layout.setContentsMargins(4, 4, 4, 4)
        self.layout.setSpacing(4)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidget(self.main_widget)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Create category containers
        self.categories = {}
        for category in ["Data Input", "Processing", "Visualization"]:
            self.categories[category] = CategoryWidget(category)
            self.layout.addWidget(self.categories[category])
        
        # Add stretch to bottom
        self.layout.addStretch()
        
        # Style the dock widget
        self.setStyleSheet("""
            QDockWidget {
                border: none;
            }
            QDockWidget::title {
                background: #f8fafc;
                padding: 8px;
                border-bottom: 1px solid #e2e8f0;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)
        
        self.setWidget(scroll)
    
    def register_components(self):
        """Register available components in their respective categories."""
        try:
            # Data Input components
            self.categories["Data Input"].add_component(
                ComponentButton("File Input", FileComponent)
            )
            
            # Processing components
            self.categories["Processing"].add_component(
                ComponentButton("DL Models", CNNComponent)
            )
            
            # Visualization components
            self.categories["Visualization"].add_component(
                ComponentButton("Graph Output", GraphComponent)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to register components: {str(e)}")
    
    def create_component(self, component_data: dict) -> Optional[WorkflowComponent]:
        """Create a component instance from the provided data."""
        try:
            self.logger.debug(f"Creating component with data: {component_data}")
            
            # Validate component data
            component_type = component_data.get("type")
            if not component_type:
                raise ValueError("No component type specified")
            
            # Get component class
            component_class = self.component_registry.get(component_type)
            if not component_class:
                raise ValueError(f"Unknown component type: {component_type}")
            
            # Create component instance
            self.logger.debug(f"Creating instance of {component_type}")
            component = component_class()
            self.component_created.emit(component)
            return component
            
        except Exception as e:
            self.logger.error(f"Failed to create component: {str(e)}")
            return None
    
    def get_registered_components(self) -> Dict[str, Type[WorkflowComponent]]:
        """Get dictionary of registered component types."""
        return self.component_registry.copy()