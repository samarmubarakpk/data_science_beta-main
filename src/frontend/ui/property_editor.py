# frontend/src/ui/property_editor.py
from PyQt5.QtWidgets import (QDockWidget, QWidget, QVBoxLayout, QFormLayout,
                           QLabel, QLineEdit, QSpinBox, QDoubleSpinBox,
                           QComboBox, QCheckBox, QPushButton, QFileDialog,
                           QScrollArea, QGroupBox, QHBoxLayout)
from PyQt5.QtCore import Qt, pyqtSlot
from typing import Optional, Dict, Any
import logging

from src.frontend.components.base import WorkflowComponent

class PropertyWidget:
    """Factory for creating property widgets based on type."""
    
    @staticmethod
    def create_widget(prop_type: str, value: Any, callback, prop_info: dict = None) -> Optional[QWidget]:
        """Create an appropriate widget for the property type."""
        if prop_type == "file":
            return PropertyWidget._create_file_widget(value, callback, prop_info)
            
        elif prop_type == "string":
            widget = QLineEdit()
            widget.setText(str(value))
            widget.textChanged.connect(callback)
            
        elif prop_type == "number":
            widget = QDoubleSpinBox()
            widget.setRange(-999999, 999999)
            widget.setDecimals(4)
            widget.setValue(float(value))
            widget.valueChanged.connect(callback)
            
        elif prop_type == "integer":
            widget = QSpinBox()
            widget.setRange(-999999, 999999)
            widget.setValue(int(value))
            widget.valueChanged.connect(callback)
            
        elif prop_type == "boolean":
            widget = QCheckBox()
            widget.setChecked(bool(value))
            widget.stateChanged.connect(lambda v: callback(bool(v)))
            
        elif prop_type == "choice":
            widget = QComboBox()
            if isinstance(value, dict):
                widget.addItems(value.get("choices", []))
                widget.setCurrentText(value.get("selected", ""))
            widget.currentTextChanged.connect(callback)
            
        else:
            return None
            
        return widget

    @staticmethod
    def _create_file_widget(value: str, callback, prop_info: dict) -> QWidget:
        """Create a file selection widget with preview."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        # File selection row
        file_row = QWidget()
        file_layout = QHBoxLayout(file_row)
        file_layout.setContentsMargins(0, 0, 0, 0)

        # Path display
        path_edit = QLineEdit()
        path_edit.setText(str(value or ""))
        path_edit.setReadOnly(True)
        file_layout.addWidget(path_edit)

        # Browse button
        browse_button = QPushButton("Browse...")
        file_layout.addWidget(browse_button)
        layout.addWidget(file_row)

        def handle_browse():
            filters = prop_info.get("filters", "All Files (*.*)")
            filename, _ = QFileDialog.getOpenFileName(
                container.window(),
                "Select File",
                str(value or ""),
                filters
            )
            if filename:
                path_edit.setText(filename)
                callback(filename)

        browse_button.clicked.connect(handle_browse)
        return container

class PropertyEditor(QDockWidget):
    """Property editor dock widget."""
    
    def __init__(self, parent=None):
        super().__init__("Properties", parent)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        # Create scroll area
        self.setMinimumWidth(300)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Create main widget and layout
        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        self.main_layout.setSpacing(8)
        
        # Create form layout for properties
        self.form_layout = QFormLayout()
        self.main_layout.addLayout(self.form_layout)
        self.main_layout.addStretch()
        
        scroll.setWidget(self.main_widget)
        self.setWidget(scroll)
        
        # Component state
        self.current_component: Optional[WorkflowComponent] = None
        self.widgets: Dict[str, QWidget] = {}
        
    @pyqtSlot(WorkflowComponent)
    def set_component(self, component: Optional[WorkflowComponent]):
        """Set the component to edit and update the property panel."""
        self.current_component = component
        self.clear_properties()
        
        if component:
            # Add component type header
            header = QLabel(f"<b>{component.__class__.__name__}</b>")
            self.form_layout.addRow(header)
            
            # Create property groups
            properties = component.get_properties()
            grouped_props = self._group_properties(properties)
            
            for group_name, group_props in grouped_props.items():
                if len(grouped_props) > 1:  # Only create groups if there are multiple
                    group_box = QGroupBox(group_name)
                    group_layout = QFormLayout()
                    self._add_properties_to_layout(group_props, group_layout)
                    group_box.setLayout(group_layout)
                    self.form_layout.addRow(group_box)
                else:
                    self._add_properties_to_layout(group_props, self.form_layout)

    def _add_properties_to_layout(self, properties: Dict[str, Any], layout: QFormLayout):
        """Add properties to the specified layout."""
        for prop_name, prop_info in properties.items():
            label = QLabel(prop_info.get("label", prop_name))
            label.setToolTip(prop_info.get("description", ""))
            
            widget = PropertyWidget.create_widget(
                prop_info.get("type", "string"),
                prop_info.get("value"),
                lambda v, name=prop_name: self._on_property_changed(name, v),
                prop_info
            )
            
            if widget:
                layout.addRow(label, widget)
                self.widgets[prop_name] = widget

    def _group_properties(self, properties: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Group properties by their group attribute."""
        grouped = {}
        for name, info in properties.items():
            group = info.get("group", "General")
            if group not in grouped:
                grouped[group] = {}
            grouped[group][name] = info
        return grouped

    def _on_property_changed(self, name: str, value: Any):
        """Handle property value changes."""
        if self.current_component:
            properties = self.current_component.get_properties()
            if name in properties:
                if properties[name]["type"] == "choice":
                    properties[name]["value"]["selected"] = value
                else:
                    properties[name]["value"] = value

                if hasattr(self.current_component, 'update'):
                    self.current_component.update()

    def clear_properties(self):
        """Clear all property widgets."""
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.widgets.clear()