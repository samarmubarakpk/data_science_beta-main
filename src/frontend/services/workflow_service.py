# frontend/src/services/workflow_service.py
from typing import Dict, Any, List, Optional
import asyncio
import aiohttp
import json
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from dataclasses import dataclass

@dataclass
class WorkflowComponent:
    id: str
    type: str
    config: Dict[str, Any]
    position: Dict[str, float]

@dataclass
class Connection:
    id: str
    source_id: str
    target_id: str
    source_port: str
    target_port: str

class WorkflowService(QObject):
    """Service layer for handling communication with backend API."""
    
    # Define signals for async operations
    workflow_loaded = pyqtSignal(dict)
    workflow_saved = pyqtSignal(str)
    component_created = pyqtSignal(dict)
    execution_started = pyqtSignal(str)
    execution_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__()
        self.base_url = base_url
        self.session = None
        
    async def init_session(self):
        """Initialize aiohttp session."""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
    async def close_session(self):
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None
            
    async def get_workflows(self) -> List[Dict[str, Any]]:
        """Get all workflows."""
        await self.init_session()
        try:
            async with self.session.get(f"{self.base_url}/api/workflows") as response:
                if response.status == 200:
                    data = await response.json()
                    return data["workflows"]
                else:
                    error_msg = await response.text()
                    self.error_occurred.emit(f"Failed to get workflows: {error_msg}")
                    return []
        except Exception as e:
            self.error_occurred.emit(f"Error getting workflows: {str(e)}")
            return []
            
    async def load_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Load a specific workflow."""
        await self.init_session()
        try:
            async with self.session.get(
                f"{self.base_url}/api/workflows/{workflow_id}"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.workflow_loaded.emit(data["workflow"])
                    return data["workflow"]
                else:
                    error_msg = await response.text()
                    self.error_occurred.emit(f"Failed to load workflow: {error_msg}")
                    return None
        except Exception as e:
            self.error_occurred.emit(f"Error loading workflow: {str(e)}")
            return None
            
    async def save_workflow(self, workflow: Dict[str, Any]) -> Optional[str]:
        """Save a workflow."""
        await self.init_session()
        try:
            if "id" in workflow:
                # Update existing workflow
                url = f"{self.base_url}/api/workflows/{workflow['id']}"
                method = self.session.put
            else:
                # Create new workflow
                url = f"{self.base_url}/api/workflows"
                method = self.session.post
                
            async with method(url, json=workflow) as response:
                if response.status in (200, 201):
                    data = await response.json()
                    workflow_id = data.get("workflow_id", workflow.get("id"))
                    self.workflow_saved.emit(workflow_id)
                    return workflow_id
                else:
                    error_msg = await response.text()
                    self.error_occurred.emit(f"Failed to save workflow: {error_msg}")
                    return None
        except Exception as e:
            self.error_occurred.emit(f"Error saving workflow: {str(e)}")
            return None
            
    async def execute_workflow(self, workflow_id: str) -> Optional[str]:
        """Execute a workflow."""
        await self.init_session()
        try:
            async with self.session.post(
                f"{self.base_url}/api/workflows/{workflow_id}/execute"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    execution_id = data["execution_id"]
                    self.execution_started.emit(execution_id)
                    return execution_id
                else:
                    error_msg = await response.text()
                    self.error_occurred.emit(f"Failed to execute workflow: {error_msg}")
                    return None
        except Exception as e:
            self.error_occurred.emit(f"Error executing workflow: {str(e)}")
            return None
            
    async def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get execution status."""
        await self.init_session()
        try:
            async with self.session.get(
                f"{self.base_url}/api/executions/{execution_id}"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data["status"] == "completed":
                        self.execution_completed.emit(data)
                    return data
                else:
                    error_msg = await response.text()
                    self.error_occurred.emit(
                        f"Failed to get execution status: {error_msg}")
                    return None
        except Exception as e:
            self.error_occurred.emit(f"Error getting execution status: {str(e)}")
            return None
            
    async def upload_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Upload a file to the backend."""
        await self.init_session()
        try:
            data = aiohttp.FormData()
            data.add_field(
                'file',
                open(file_path, 'rb'),
                filename=file_path.name
            )
            
            async with self.session.post(
                f"{self.base_url}/api/data/upload",
                data=data
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_msg = await response.text()
                    self.error_occurred.emit(f"Failed to upload file: {error_msg}")
                    return None
        except Exception as e:
            self.error_occurred.emit(f"Error uploading file: {str(e)}")
            return None

class AsyncWorkflowRunner(QThread):
    """Thread runner for executing async workflow operations."""
    
    def __init__(self, coro, parent=None):
        super().__init__(parent)
        self.coro = coro
        
    def run(self):
        """Execute the coroutine in a new event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.coro)
        finally:
            loop.close()