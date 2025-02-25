from asyncio import Queue
from sqlite3 import Connection
from typing import Dict, List, Optional, Any, Tuple
import networkx as nx
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass
import logging
import json
from pathlib import Path
from threading import Lock
from PyQt5.QtCore import QObject, pyqtSignal
import datetime
from ..components.base_component import BaseComponent
from ..core.data_manager import DataManager


@dataclass
class ExecutionNode:
    """Represents a node in the execution graph."""
    component: BaseComponent
    dependencies: List[BaseComponent]
    dependents: List[BaseComponent]

class WorkflowEngine:
    """Handles the execution of the workflow graph."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def execute(self, components: Dict[str, BaseComponent],
                connections: List[Tuple[BaseComponent, BaseComponent]]) -> Dict[str, Any]:
        """Execute the workflow in the correct order."""
        try:
            # Build execution graph
            execution_graph = self._build_execution_graph(components, connections)
            
            # Sort components in execution order
            execution_order = self._topological_sort(execution_graph)
            
            # Execute components in order
            results = {}
            for component in execution_order:
                try:
                    # Get input data from dependencies
                    input_data = self._gather_inputs(component, execution_graph, results)
                    
                    # Set component inputs
                    for port_name, data in input_data.items():
                        component.input_ports[port_name] = data
                    
                    # Execute component
                    component_result = component.process()
                    results[component.instance_id] = component_result
                    
                    # Log success
                    self.logger.info(f"Executed component {component.__class__.__name__}")
                    
                except Exception as e:
                    self.logger.error(f"Component execution failed: {str(e)}")
                    results[component.instance_id] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {str(e)}")
            raise
            
    def _build_execution_graph(self, components: Dict[str, BaseComponent],
                             connections: List[Tuple[BaseComponent, BaseComponent]]) -> Dict[BaseComponent, ExecutionNode]:
        """Build a graph representation of the workflow."""
        # Initialize execution nodes
        graph = {
            component: ExecutionNode(component, [], [])
            for component in components.values()
        }
        
        # Add connections
        for source, target in connections:
            graph[source].dependents.append(target)
            graph[target].dependencies.append(source)
            
        return graph
        
    def _topological_sort(self, graph: Dict[BaseComponent, ExecutionNode]) -> List[BaseComponent]:
        """Sort components in execution order using topological sort."""
        # Calculate in-degrees
        in_degree = {
            component: len(node.dependencies)
            for component, node in graph.items()
        }
        
        # Find components with no dependencies
        queue = Queue()
        for component, degree in in_degree.items():
            if degree == 0:
                queue.put(component)
                
        # Process queue
        execution_order = []
        while not queue.empty():
            component = queue.get()
            execution_order.append(component)
            
            # Update in-degrees of dependent components
            node = graph[component]
            for dependent in node.dependents:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.put(dependent)
                    
        # Check for cycles
        if len(execution_order) != len(graph):
            raise ValueError("Workflow contains cycles")
            
        return execution_order
        
    def _gather_inputs(self, component: BaseComponent,
                      graph: Dict[BaseComponent, ExecutionNode],
                      results: Dict[str, Any]) -> Dict[str, Any]:
        """Gather input data from dependencies."""
        inputs = {}
        node = graph[component]
        
        # Get outputs from each dependency
        for dependency in node.dependencies:
            dependency_result = results[dependency.instance_id]
            
            # Map outputs to inputs based on port types
            for out_name, out_value in dependency_result.items():
                for in_name, in_port in component.input_ports.items():
                    if in_port["type"] == dependency.output_ports[out_name]["type"]:
                        inputs[in_name] = out_value
                        break
                        
        return inputs
        
    def validate_workflow(self, components: Dict[str, BaseComponent],
                         connections: List[Tuple[BaseComponent, BaseComponent]]) -> List[str]:
        """Validate the workflow before execution."""
        issues = []
        
        try:
            # Build execution graph
            graph = self._build_execution_graph(components, connections)
            
            # Check for cycles
            try:
                self._topological_sort(graph)
            except ValueError:
                issues.append("Workflow contains cycles")
                
            # Validate each component
            for component in components.values():
                # Check required inputs are connected
                for input_name in component.get_required_inputs():
                    if not any(target == component and input_name in inputs 
                             for _, target, inputs in connections):
                        issues.append(
                            f"{component.__class__.__name__}: Required input '{input_name}' not connected"
                        )
                
                # Validate component-specific rules
                if hasattr(component, 'validate'):
                    component_issues = component.validate()
                    issues.extend(component_issues)
                    
            return issues
            
        except Exception as e:
            self.logger.error(f"Workflow validation failed: {str(e)}")
            issues.append(f"Validation error: {str(e)}")
            return issues
    def _validate_connection(self, connection: Connection) -> bool:
        """Validate a connection between components."""
        try:
            if connection.source_id not in self.components:
                raise ValueError("Source component not found")
            if connection.target_id not in self.components:
                raise ValueError("Target component not found")
                
            source_component = self.components[connection.source_id]
            target_component = self.components[connection.target_id]
            
            # Validate ports
            if not source_component.has_output(connection.source_port):
                raise ValueError(f"Invalid source port: {connection.source_port}")
            if not target_component.has_input(connection.target_port):
                raise ValueError(f"Invalid target port: {connection.target_port}")
                
            # Check port compatibility
            if not source_component.can_connect_to(target_component, 
                                                 connection.source_port,
                                                 connection.target_port):
                raise ValueError("Incompatible ports")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Connection validation failed: {str(e)}")
            return False

    def save_workflow(self, filepath: str) -> bool:
        """Save the current workflow state to a file."""
        try:
            workflow_state = {
                "components": {
                    comp_id: {
                        "type": comp.__class__.__name__,
                        "state": comp.get_status()
                    }
                    for comp_id, comp in self.components.items()
                },
                "connections": [
                    {
                        "source_id": edge[0],
                        "target_id": edge[1],
                        "source_port": self.graph.edges[edge]["source_port"],
                        "target_port": self.graph.edges[edge]["target_port"]
                    }
                    for edge in self.graph.edges
                ],
                "metadata": {
                    "version": "1.0",
                    "created_at": str(datetime.now())
                }
            }
            
            if self.data_manager:
                return self.data_manager.save_workflow(workflow_state, filepath)
            else:
                with open(filepath, 'w') as f:
                    json.dump(workflow_state, f, indent=2)
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to save workflow: {str(e)}")
            return False

    def load_workflow(self, filepath: str) -> bool:
        """Load a workflow from a file."""
        try:
            # Load workflow data
            if self.data_manager:
                workflow_data = self.data_manager.load_workflow(filepath)
            else:
                with open(filepath, 'r') as f:
                    workflow_data = json.load(f)
                    
            if not workflow_data:
                return False
                
            # Clear current workflow
            self.clear_workflow()
            
            # Recreate components and connections
            for comp_id, comp_data in workflow_data["components"].items():
                # Component recreation logic here
                pass
                
            for conn_data in workflow_data["connections"]:
                self.connect_components(Connection(**conn_data))
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load workflow: {str(e)}")
            return False

    def clear_workflow(self) -> None:
        """Clear the current workflow state."""
        try:
            # Cancel any pending executions
            self._cancel_all_executions()
            
            # Cleanup components
            for component in self.components.values():
                component.cleanup()
                
            self.components.clear()
            self.graph.clear()
            
        except Exception as e:
            self.logger.error(f"Failed to clear workflow: {str(e)}")

    def _cancel_component_execution(self, component_id: str) -> None:
        """Cancel pending execution for a component."""
        for future in self._futures:
            if not future.done():
                future.cancel()

    def _cancel_all_executions(self) -> None:
        """Cancel all pending executions."""
        for future in self._futures:
            if not future.done():
                future.cancel()
        self._futures.clear()
        self._is_executing = False