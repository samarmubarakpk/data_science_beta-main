# src/core/component_bridge.py
from typing import Dict, Optional, Any
import logging

from src.backend.components.base_component import BaseComponent
from src.frontend.components.base import WorkflowComponent
from src.backend.components.input_component import FileComponent as BackendFileComponent
from src.backend.components.output_component import OutputComponent as BackendGraphComponent
from src.backend.components.cnn_component import CNNComponent as BackendCNNComponent

class ComponentBridge:
    """Manages the connection between frontend and backend components."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.component_pairs = {}
        
        # Register component mappings
        self.frontend_to_backend = {
            'FileComponent': BackendFileComponent,
            'GraphComponent': BackendGraphComponent,
            'CNNComponent': BackendCNNComponent
        }
    
    def register_component(self, frontend_component: WorkflowComponent) -> bool:
        """Create and register a backend component for a frontend component."""
        try:
            # Create corresponding backend component
            backend_class = self.frontend_to_backend.get(
                frontend_component.__class__.__name__
            )
            if not backend_class:
                return False
            
            # Initialize backend component with frontend properties
            backend_component = backend_class(config=frontend_component.get_properties())
            
            # Store the pair
            self.component_pairs[frontend_component.id] = {
                'frontend': frontend_component,
                'backend': backend_component
            }
            
            # Connect signals
            backend_component.status_changed.connect(
                lambda status: self._handle_status_change(frontend_component.id, status)
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register component: {str(e)}")
            return False

    def _handle_status_change(self, component_id: str, status: str):
        """Handle status changes from backend component."""
        pair = self.component_pairs.get(component_id)
        if pair:
            # Update frontend visualization based on status
            frontend = pair['frontend']
            frontend.update_status(status)

    def sync_properties(self, frontend_id: str, properties: Dict[str, Any]) -> bool:
        """Synchronize properties between frontend and backend components."""
        pair = self.component_pairs.get(frontend_id)
        if not pair:
            return False
            
        try:
            backend = pair['backend']
            backend.config.update(properties)
            return True
        except Exception as e:
            self.logger.error(f"Failed to sync properties: {str(e)}")
            return False

    def execute_workflow(self, execution_order: list) -> Dict[str, Any]:
        """Execute the workflow in the specified order."""
        results = {}
        
        for component_id in execution_order:
            pair = self.component_pairs.get(component_id)
            if not pair:
                continue
                
            try:
                # Execute backend component
                backend = pair['backend']
                result = backend.process()
                
                # Update frontend visualization
                frontend = pair['frontend']
                frontend.update_results(result)
                
                results[component_id] = result
                
            except Exception as e:
                self.logger.error(f"Component execution failed: {str(e)}")
                results[component_id] = {"error": str(e)}
                
        return results

    def validate_connection(self, source_id: str, target_id: str,
                          source_port: str, target_port: str) -> bool:
        """Validate if two components can be connected."""
        source_pair = self.component_pairs.get(source_id)
        target_pair = self.component_pairs.get(target_id)
        
        if not (source_pair and target_pair):
            return False
            
        source_backend = source_pair['backend']
        target_backend = target_pair['backend']
        
        return source_backend.can_connect_to(target_backend, source_port, target_port)