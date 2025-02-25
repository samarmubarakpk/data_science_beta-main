# src/backend/components/base_component.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import uuid
from dataclasses import dataclass
import logging
from PyQt5.QtCore import QObject, pyqtSignal

@dataclass
class ComponentMetadata:
    """Metadata for component registration and display."""
    id: str
    name: str
    description: str
    version: str
    category: str
    input_ports: Dict[str, Dict[str, Any]] = None
    output_ports: Dict[str, Dict[str, Any]] = None

# Create an intermediate class to resolve metaclass conflict
class ComponentABC(ABC):
    pass


@dataclass
class ComponentMetadata:
    """Metadata for component registration and display."""
    id: str
    name: str
    description: str
    version: str
    category: str
    input_ports: Dict[str, Dict[str, Any]] = None
    output_ports: Dict[str, Dict[str, Any]] = None

# Create a metaclass that combines Qt and ABC metaclasses
class ComponentMetaclass(type(QObject), type(ABC)):
    pass

# Use the combined metaclass
class BaseComponent(QObject, ABC, metaclass=ComponentMetaclass):
    """Enhanced base class for all workflow components."""
    
    # Define signals for component status updates
    status_changed = pyqtSignal(str)  # New status
    progress_updated = pyqtSignal(int)  # Progress percentage
    error_occurred = pyqtSignal(str)  # Error message
    execution_completed = pyqtSignal(dict)  # Results
    
    def __init__(self, config: Dict[str, Any] = None):
        QObject.__init__(self)
        self.instance_id = str(uuid.uuid4())
        self.config = config or {}
        self.input_ports: Dict[str, Any] = {}
        self.output_ports: Dict[str, Any] = {}
        self._status = "initialized"
        self._progress = 0
        self._error = None
        self.metadata: ComponentMetadata = None  # Will be set by subclasses
        self.logger = logging.getLogger(self.__class__.__name__)
        
    @property
    def status(self) -> str:
        """Get current component status."""
        return self._status
        
    @status.setter
    def status(self, value: str):
        """Set component status and emit signal."""
        self._status = value
        self.status_changed.emit(value)
        self.logger.info(f"Component {self.instance_id} status: {value}")
        
    @property
    def progress(self) -> int:
        """Get current progress percentage."""
        return self._progress
        
    @progress.setter
    def progress(self, value: int):
        """Set progress and emit signal."""
        self._progress = max(0, min(100, value))  # Clamp between 0-100
        self.progress_updated.emit(self._progress)
        
    def set_error(self, error_message: str):
        """Set error state and emit signal."""
        self._error = error_message
        self.status = "error"
        self.error_occurred.emit(error_message)
        self.logger.error(f"Component {self.instance_id} error: {error_message}")
        
    def add_input_port(self, name: str, port_type: str, description: str = "") -> None:
        """Add an input port to the component."""
        if not self.metadata:
            self.metadata = ComponentMetadata("", "", "", "", "")
        if not self.metadata.input_ports:
            self.metadata.input_ports = {}
            
        self.metadata.input_ports[name] = {
            "type": port_type,
            "description": description
        }
        self.input_ports[name] = None
        
    def add_output_port(self, name: str, port_type: str, description: str = "") -> None:
        """Add an output port to the component."""
        if not self.metadata:
            self.metadata = ComponentMetadata("", "", "", "", "")
        if not self.metadata.output_ports:
            self.metadata.output_ports = {}
            
        self.metadata.output_ports[name] = {
            "type": port_type,
            "description": description
        }
        self.output_ports[name] = None
        
    def set_input(self, port_name: str, value: Any) -> bool:
        """Set value for an input port."""
        if port_name not in self.metadata.input_ports:
            self.set_error(f"Invalid input port: {port_name}")
            return False
            
        try:
            self.input_ports[port_name] = value
            return True
        except Exception as e:
            self.set_error(f"Failed to set input {port_name}: {str(e)}")
            return False
            
    def get_output(self, port_name: str) -> Optional[Any]:
        """Get value from an output port."""
        return self.output_ports.get(port_name)
        
    def has_output(self, port_name: str) -> bool:
        """Check if an output port has a value."""
        return port_name in self.output_ports and self.output_ports[port_name] is not None
        
    @abstractmethod
    def process(self) -> Dict[str, Any]:
        """Process the component's inputs and produce outputs."""
        pass
        
    def validate_inputs(self) -> bool:
        """Validate that all required inputs are connected and valid."""
        try:
            required_inputs = self.get_required_inputs()
            for port_name in required_inputs:
                if port_name not in self.input_ports:
                    raise ValueError(f"Required input port missing: {port_name}")
                if self.input_ports[port_name] is None:
                    raise ValueError(f"Required input port not connected: {port_name}")
                    
            return True
        except Exception as e:
            self.set_error(f"Input validation failed: {str(e)}")
            return False
        
    @abstractmethod
    def get_required_inputs(self) -> List[str]:
        """Get list of required input ports."""
        pass
        
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the component."""
        return {
            "id": self.instance_id,
            "status": self.status,
            "progress": self.progress,
            "error": self._error,
            "config": self.config,
            "input_ports": {
                name: {
                    "type": self.metadata.input_ports[name]["type"],
                    "description": self.metadata.input_ports[name]["description"],
                    "connected": value is not None
                }
                for name, value in self.input_ports.items()
            },
            "output_ports": {
                name: {
                    "type": self.metadata.output_ports[name]["type"],
                    "description": self.metadata.output_ports[name]["description"],
                    "has_value": self.has_output(name)
                }
                for name in self.output_ports
            },
            "metadata": self.metadata.__dict__ if self.metadata else None
        }
        
    def cleanup(self):
        """Clean up any resources used by the component."""
        self.input_ports.clear()
        self.output_ports.clear()
        self.status = "cleaned"
        
    def reset(self):
        """Reset component to initial state."""
        self.input_ports = {name: None for name in self.metadata.input_ports}
        self.output_ports = {name: None for name in self.metadata.output_ports}
        self._progress = 0
        self._error = None
        self.status = "initialized"
        
    def can_connect_to(self, other: 'BaseComponent', my_port: str, other_port: str) -> bool:
        """Check if this component can connect to another component."""
        if not self.metadata or not other.metadata:
            return False
            
        # Get port types
        if my_port in self.metadata.output_ports:
            my_port_type = self.metadata.output_ports[my_port]["type"]
            other_port_type = other.metadata.input_ports.get(other_port, {}).get("type")
        elif my_port in self.metadata.input_ports:
            my_port_type = self.metadata.input_ports[my_port]["type"]
            other_port_type = other.metadata.output_ports.get(other_port, {}).get("type")
        else:
            return False
            
        # Check port type compatibility
        return my_port_type == other_port_type or my_port_type == "any" or other_port_type == "any"