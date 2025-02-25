# backend/src/components/__init__.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import uuid

@dataclass
class BaseComponent(ABC):
    """Base class for all workflow components."""
    
    name: str
    instance_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    input_ports: Dict[str, str] = field(default_factory=dict)
    output_ports: Dict[str, str] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
    
    @abstractmethod
    def process(self) -> Optional[Dict[str, Any]]:
        """Process the component's inputs and return results."""
        pass
    
    @abstractmethod
    def validate_inputs(self) -> bool:
        """Validate that all required inputs are available."""
        pass
    
    def cleanup(self) -> None:
        """Clean up any resources used by the component."""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the component."""
        return {
            "id": self.instance_id,
            "name": self.name,
            "input_ports": self.input_ports,
            "output_ports": self.output_ports,
            "config": self.config
        }