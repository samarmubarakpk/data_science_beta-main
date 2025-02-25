# from typing import Dict, List, Type, Optional
# from ..components.base_component import BaseComponent  # Direct import
# import importlib
# import inspect
# import logging

# class ComponentManager:
#     """Manages component registration and instantiation."""
    
#     def __init__(self):
#         self._component_types: Dict[str, Type[BaseComponent]] = {}
#         self.logger = logging.getLogger(__name__)

#     def register_component(self, component_type: str, component_class: Type[BaseComponent]) -> bool:
#         """Register a new component type."""
#         try:
#             if not inspect.isclass(component_class) or not issubclass(component_class, BaseComponent):
#                 raise ValueError("Component must inherit from BaseComponent")
                
#             self._component_types[component_type] = component_class
#             return True
#         except Exception as e:
#             self.logger.error(f"Failed to register component: {str(e)}")
#             return False

#     def create_component(self, component_type: str, config: Dict) -> Optional[BaseComponent]:
#         """Create a new instance of a component type."""
#         try:
#             if component_type not in self._component_types:
#                 raise ValueError(f"Unknown component type: {component_type}")
                
#             component_class = self._component_types[component_type]
#             return component_class(**config)
#         except Exception as e:
#             self.logger.error(f"Failed to create component: {str(e)}")
#             return None

#     def get_available_components(self) -> List[Dict]:
#         """Get list of all registered component types."""
#         return [
#             {
#                 "type": comp_type,
#                 "name": comp_class.__name__,
#                 "description": comp_class.__doc__ or "",
#                 "input_ports": self._get_default_ports(comp_class, "input_ports"),
#                 "output_ports": self._get_default_ports(comp_class, "output_ports")
#             }
#             for comp_type, comp_class in self._component_types.items()
#         ]

#     def _get_default_ports(self, component_class: Type[BaseComponent], port_type: str) -> Dict:
#         """Get the default ports for a component class."""
#         try:
#             # Create temporary instance to get default ports
#             temp_instance = component_class(name="temp")
#             return getattr(temp_instance, port_type)
#         except:
#             return {}