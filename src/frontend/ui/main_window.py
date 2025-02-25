from PyQt5.QtWidgets import (
    QMainWindow, QDockWidget, QToolBar, QStatusBar, QAction,
    QFileDialog, QMessageBox, QMenu, QShortcut, QProgressDialog
)
from PyQt5.QtCore import Qt, QSettings, QSize, QTimer
from PyQt5.QtGui import QIcon, QKeySequence
from pathlib import Path

from src.backend.utils.loggers import get_logger

from .canvas import ConnectionLine, WorkflowCanvas
from .component_palette import ComponentPalette
from .property_editor import PropertyEditor
from ..components.base import WorkflowComponent


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize logger
        self.logger = get_logger(__name__)
        
        # Initialize variables
        self.current_file = None  # Add this line
        self.canvas = None
        self.component_palette = None
        self.property_editor = None
        
        # Initialize UI components
        self.settings = QSettings('YourCompany', 'DataMiningApp')
        
        # Create the status bar first
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Setup UI
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Data Mining Workflow Designer")
        self.setMinimumSize(1024, 768)
        
        # Create dock widgets first
        self.create_dock_widgets()
        
        # Create toolbar and menus
        self.create_toolbar()
        self.create_menus()
        
    def create_dock_widgets(self):
        """Create and setup dock widgets."""
        try:
            # Create canvas first
            self.canvas = WorkflowCanvas(self)
            self.setCentralWidget(self.canvas)
            
            # Component palette
            self.component_palette = ComponentPalette(self)
            self.addDockWidget(Qt.LeftDockWidgetArea, self.component_palette)
            
            # Property editor
            self.property_editor = PropertyEditor(self)
            self.addDockWidget(Qt.RightDockWidgetArea, self.property_editor)
            
            # Connect signals - make sure types match!
            self.canvas.component_selected.connect(self.property_editor.set_component)
            self.canvas.status_message.connect(self.statusBar().showMessage)
            self.component_palette.component_created.connect(self.canvas.add_component)
            
        except Exception as e:
            self.logger.error(f"Failed to create dock widgets: {str(e)}")
            raise

    def update_window_title(self):
        """Update window title with modification status."""
        title = "Data Mining Workflow Designer"
        if self.current_file:
            title += f" - {Path(self.current_file).name}"
        if self.canvas and self.canvas.modified:  # Use the property instead of the method
            title += " *"
        self.setWindowTitle(title)

    def create_toolbar(self):
        """Create the main toolbar."""
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        
        # Add standard actions
        actions = [
            ("New", ":/icons/new.png", self.new_workflow),
            ("Open", ":/icons/open.png", self.open_workflow),
            ("Save", ":/icons/save.png", self.save_workflow),
        ]
        
        for name, icon, handler in actions:
            action = QAction(QIcon(icon), name, self)
            action.triggered.connect(handler)
            toolbar.addAction(action)
            
    def create_menus(self):
        """Create application menus."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        actions = [
            ("&New", QKeySequence.New, self.new_workflow),
            ("&Open...", QKeySequence.Open, self.open_workflow),
            ("&Save", QKeySequence.Save, self.save_workflow),
            ("Save &As...", "Ctrl+Shift+S", self.save_workflow_as)
        ]
        
        for name, shortcut, handler in actions:
            action = file_menu.addAction(name)
            if isinstance(shortcut, str):
                action.setShortcut(QKeySequence(shortcut))
            else:
                action.setShortcut(shortcut)
            action.triggered.connect(handler)
            
        file_menu.addSeparator()
        
        # Recent files submenu
        self.recent_menu = QMenu("Recent Files", self)
        file_menu.addMenu(self.recent_menu)
        
        file_menu.addSeparator()
        exit_action = file_menu.addAction("E&xit")
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        
    def setup_connections(self):
        """Setup additional signal/slot connections."""
        if self.canvas:
            self.canvas.modified_changed.connect(self.update_window_title)
            
    def setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        QShortcut(QKeySequence.New, self, self.new_workflow)
        QShortcut(QKeySequence.Open, self, self.open_workflow)
        QShortcut(QKeySequence.Save, self, self.save_workflow)
        
    def setup_autosave(self):
        """Setup autosave timer."""
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.autosave)
        self.autosave_timer.start(300000)  # 5 minutes
        
    def new_workflow(self):
        """Create new workflow."""
        if self.check_unsaved_changes():
            self.canvas.clear()
            self.current_file = None
            self.update_window_title()
            
    def open_workflow(self, filename=None):
        """Open workflow from file."""
        if not filename:
            filename, _ = QFileDialog.getOpenFileName(
                self, "Open Workflow",
                str(Path.home()),
                "Workflow Files (*.workflow);;All Files (*)"
            )
        if filename and self.canvas:
            if self.canvas.load_from_file(filename):
                self.current_file = filename
                self.update_window_title()
                
    def save_workflow(self, filename=None):
        """Save current workflow."""
        if not filename and not self.current_file:
            return self.save_workflow_as()
            
        filename = filename or self.current_file
        if filename and self.canvas:
            if self.canvas.save_to_file(filename):
                self.current_file = filename
                self.update_window_title()
                return True
        return False
        
    def save_workflow_as(self):
        """Save workflow with a new filename."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Workflow As",
            str(Path.home()),
            "Workflow Files (*.workflow);;All Files (*)"
        )
        if filename:
            return self.save_workflow(filename)
        return False
        
    def autosave(self):
        """Perform autosave if needed."""
        if self.current_file and self.canvas and self.canvas.is_modified():
            self.save_workflow(self.current_file)
            self.status_bar.showMessage("Autosaved", 2000)
            
    def check_unsaved_changes(self) -> bool:
        """Check for unsaved changes."""
        if self.canvas and self.canvas.is_modified():
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "Save changes before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            if reply == QMessageBox.Save:
                return self.save_workflow()
            elif reply == QMessageBox.Cancel:
                return False
        return True
        
    def load_window_state(self):
        """Load window geometry and state."""
        geometry = self.settings.value('geometry')
        if geometry:
            self.restoreGeometry(geometry)
            
    def update_window_title(self):
        """Update window title."""
        title = "Data Mining Workflow Designer"
        if self.current_file:
            title += f" - {Path(self.current_file).name}"
        if self.canvas and self.canvas.is_modified():
            title += " *"
        self.setWindowTitle(title)
        
    def closeEvent(self, event):
        """Handle application close."""
        if self.check_unsaved_changes():
            self.settings.setValue('geometry', self.saveGeometry())
            event.accept()
        else:
            event.ignore()

    def check_unsaved_changes(self) -> bool:
        """Check for unsaved changes and prompt user if necessary."""
        if self.canvas and self.canvas.modified:  # Use the property instead of method
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "The workflow has unsaved changes. Would you like to save them?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Save:
                return self.save_workflow()
            elif reply == QMessageBox.Cancel:
                return False
                
        return True
    
    # In main_window.py
    def setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Delete shortcut
        delete_shortcut = QShortcut(QKeySequence.Delete, self)
        delete_shortcut.activated.connect(self.delete_selected)
        
        # Add other shortcuts as needed
        
    def delete_selected(self):
        """Delete selected items on the canvas."""
        if self.canvas:
            self.canvas.delete_selected_items()

    def save_to_file(self, filename: str) -> bool:
        """Save the workflow to a file."""
        try:
            print("Canvas: Saving workflow to file...")
            
            # Create workflow data structure
            workflow_data = {
                'components': {},
                'connections': []
            }
            
            # Save components
            for comp_id, component in self.components.items():
                print(f"Canvas: Saving component {component.title}")
                component_data = {
                    'type': component.__class__.__name__,
                    'position': {
                        'x': component.pos().x(),
                        'y': component.pos().y()
                    },
                    'properties': component.properties,
                    'id': comp_id
                }
                workflow_data['components'][comp_id] = component_data

            # Save connections
            for connection in self.connections:
                print("Canvas: Saving connection")
                connection_data = {
                    'source': {
                        'component': connection.start_port.parent().id,
                        'port': connection.start_port.name
                    },
                    'target': {
                        'component': connection.end_port.parent().id,
                        'port': connection.end_port.name
                    }
                }
                workflow_data['connections'].append(connection_data)

            # Save to file
            import json
            with open(filename, 'w') as f:
                json.dump(workflow_data, f, indent=4)
                
            print(f"Canvas: Workflow saved successfully to {filename}")
            self.modified = False  # Reset modified flag
            return True

        except Exception as e:
            print(f"Canvas ERROR in save_to_file: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def load_from_file(self, filename: str) -> bool:
        """Load workflow from a file."""
        try:
            print(f"Canvas: Loading workflow from {filename}")
            
            # Clear current workflow
            self.clear(save_state=False)
            
            # Load file
            import json
            with open(filename, 'r') as f:
                workflow_data = json.load(f)
                
            # Create components
            for comp_id, comp_data in workflow_data['components'].items():
                print(f"Canvas: Creating component of type {comp_data['type']}")
                
                # Create component instance
                component = self.create_component({'type': comp_data['type']})
                if component:
                    # Set component ID and position
                    component.id = comp_id
                    component.setPos(
                        comp_data['position']['x'],
                        comp_data['position']['y']
                    )
                    
                    # Set properties
                    if 'properties' in comp_data:
                        component.properties = comp_data['properties']
                    
                    # Add to canvas
                    self.add_component(component, save_state=False)

            # Create connections
            for conn_data in workflow_data['connections']:
                print("Canvas: Restoring connection")
                try:
                    # Get source component and port
                    source_comp = self.components[conn_data['source']['component']]
                    source_port = source_comp.output_ports[conn_data['source']['port']]
                    
                    # Get target component and port
                    target_comp = self.components[conn_data['target']['component']]
                    target_port = target_comp.input_ports[conn_data['target']['port']]
                    
                    # Create connection
                    connection = ConnectionLine(source_port, target_port)
                    self.scene.addItem(connection)
                    self.connections.add(connection)
                    connection.update_position()
                    
                except Exception as e:
                    print(f"Canvas ERROR: Failed to restore connection: {str(e)}")
                    continue

            self.modified = False
            print("Canvas: Workflow loaded successfully")
            return True

        except Exception as e:
            print(f"Canvas ERROR in load_from_file: {str(e)}")
            import traceback
            traceback.print_exc()
            return False