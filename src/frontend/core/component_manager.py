# frontend/src/core/component_manager.py
from typing import Dict, Type, Optional
from ..components.base import WorkflowComponent
from ..components.file_component import FileComponent
from ..components.graph_component import GraphComponent
from ..components.cnn_component import CNNComponent

class ComponentManager:
    """Manages component registration and creation."""
    
    def __init__(self):
        self.component_types: Dict[str, Type[WorkflowComponent]] = {}
        self.register_default_components()
        
    def register_default_components(self):
        """Register built-in components."""
        self.register_component("file", FileComponent)
        self.register_component("graph", GraphComponent)
        self.register_component("cnn", CNNComponent)
        
    def register_component(self, type_name: str, component_class: Type[WorkflowComponent]):
        """Register a new component type."""
        self.component_types[type_name] = component_class
        
    def create_component(self, type_name: str) -> Optional[WorkflowComponent]:
        """Create a new component instance."""
        component_class = self.component_types.get(type_name)
        if component_class:
            return component_class()
        return None
        
    def get_component_types(self) -> Dict[str, Dict]:
        """Get information about available component types."""
        return {
            type_name: {
                "name": component_class.__name__,
                "description": component_class.__doc__ or "",
                "category": getattr(component_class, "category", "Misc")
            }
            for type_name, component_class in self.component_types.items()
        }