from typing import Dict, Any, Optional, List, Union
import os
import json
import shutil
from pathlib import Path
import logging
import time
from datetime import datetime, timedelta
from PyQt5.QtCore import QObject, pyqtSignal
import hashlib

class DataManager(QObject):
    """Enhanced manager for workflow data storage and retrieval."""
    
    # Define signals
    storage_error = pyqtSignal(str)  # Error message
    cleanup_completed = pyqtSignal(int)  # Number of files cleaned
    
    def __init__(self, base_path: str = "./data"):
        super().__init__()
        self.base_path = Path(base_path)
        self.logger = logging.getLogger(__name__)
        
        # Create directory structure
        self.directories = {
            "uploads": self.base_path / "uploads",
            "workflows": self.base_path / "workflows",
            "models": self.base_path / "models",
            "results": self.base_path / "results",
            "temp": self.base_path / "temp",
            "cache": self.base_path / "cache"
        }
        
        self._init_directories()
        
    def _init_directories(self) -> None:
        """Initialize directory structure."""
        try:
            for dir_path in self.directories.values():
                dir_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.logger.error(f"Failed to initialize directories: {str(e)}")
            self.storage_error.emit(str(e))

    def save_file(self, file_data: Union[bytes, Path], filename: str, 
                 category: str = "uploads") -> Optional[str]:
        """Save a file to the appropriate directory."""
        try:
            if category not in self.directories:
                raise ValueError(f"Invalid category: {category}")
                
            # Generate unique filename if needed
            file_path = self._get_unique_path(self.directories[category], filename)
            
            # Save file
            if isinstance(file_data, bytes):
                with open(file_path, "wb") as f:
                    f.write(file_data)
            else:
                shutil.copy2(file_data, file_path)
                
            self.logger.info(f"Saved file: {file_path}")
            return str(file_path)
            
        except Exception as e:
            self.logger.error(f"Failed to save file: {str(e)}")
            self.storage_error.emit(f"Failed to save file: {str(e)}")
            return None

    def get_file(self, file_id: str, category: str = "uploads") -> Optional[bytes]:
        """Retrieve a file by its ID and category."""
        try:
            if category not in self.directories:
                raise ValueError(f"Invalid category: {category}")
                
            file_path = self.directories[category] / file_id
            if not file_path.exists():
                return None
                
            with open(file_path, "rb") as f:
                return f.read()
                
        except Exception as e:
            self.logger.error(f"Failed to retrieve file: {str(e)}")
            self.storage_error.emit(f"Failed to retrieve file: {str(e)}")
            return None

    def save_workflow(self, workflow_data: Dict[str, Any], workflow_id: str) -> bool:
        """Save workflow data with component states."""
        try:
            # Add metadata
            workflow_data["metadata"] = {
                "created": datetime.now().isoformat(),
                "version": "1.0",
                "last_modified": datetime.now().isoformat()
            }
            
            file_path = self.directories["workflows"] / f"{workflow_id}.json"
            
            # Create backup if file exists
            if file_path.exists():
                backup_path = self._create_backup(file_path)
                self.logger.info(f"Created backup: {backup_path}")
            
            # Save workflow
            with open(file_path, "w") as f:
                json.dump(workflow_data, f, indent=2)
                
            self.logger.info(f"Saved workflow: {workflow_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save workflow: {str(e)}")
            self.storage_error.emit(f"Failed to save workflow: {str(e)}")
            return False

    def load_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Load workflow data with validation."""
        try:
            file_path = self.directories["workflows"] / f"{workflow_id}.json"
            if not file_path.exists():
                return None
                
            with open(file_path, "r") as f:
                workflow_data = json.load(f)
                
            # Validate workflow data
            if not self._validate_workflow_data(workflow_data):
                raise ValueError("Invalid workflow data format")
                
            return workflow_data
            
        except Exception as e:
            self.logger.error(f"Failed to load workflow: {str(e)}")
            self.storage_error.emit(f"Failed to load workflow: {str(e)}")
            return None

    def save_model(self, model_data: bytes, model_id: str) -> Optional[str]:
        """Save a trained model."""
        return self.save_file(model_data, f"{model_id}.pth", "models")

    def load_model(self, model_id: str) -> Optional[bytes]:
        """Load a trained model."""
        return self.get_file(f"{model_id}.pth", "models")

    def save_results(self, results_data: Dict[str, Any], result_id: str) -> bool:
        """Save processing results."""
        try:
            file_path = self.directories["results"] / f"{result_id}.json"
            with open(file_path, "w") as f:
                json.dump(results_data, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Failed to save results: {str(e)}")
            self.storage_error.emit(f"Failed to save results: {str(e)}")
            return False

    def cleanup_old_files(self, max_age_days: int = 7) -> None:
        """Clean up old files from all directories."""
        try:
            cleaned_count = 0
            current_time = time.time()
            max_age = timedelta(days=max_age_days).total_seconds()
            
            # Clean up each directory
            for category, dir_path in self.directories.items():
                if category == "workflows":  # Skip workflow files
                    continue
                    
                for file_path in dir_path.glob("*"):
                    if file_path.is_file():
                        file_age = current_time - file_path.stat().st_mtime
                        if file_age > max_age:
                            file_path.unlink()
                            cleaned_count += 1
                            
            self.logger.info(f"Cleaned up {cleaned_count} old files")
            self.cleanup_completed.emit(cleaned_count)
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {str(e)}")
            self.storage_error.emit(f"Cleanup failed: {str(e)}")

    def _get_unique_path(self, directory: Path, filename: str) -> Path:
        """Generate a unique file path in the given directory."""
        stem = Path(filename).stem
        suffix = Path(filename).suffix
        counter = 0
        
        while True:
            if counter == 0:
                file_path = directory / filename
            else:
                file_path = directory / f"{stem}_{counter}{suffix}"
                
            if not file_path.exists():
                return file_path
            counter += 1

    def _create_backup(self, file_path: Path) -> Path:
        """Create a backup of the given file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.parent / f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"
        shutil.copy2(file_path, backup_path)
        return backup_path

    def _validate_workflow_data(self, data: Dict[str, Any]) -> bool:
        """Validate workflow data structure."""
        required_keys = {"components", "connections", "metadata"}
        return all(key in data for key in required_keys)

    def get_available_workflows(self) -> List[Dict[str, Any]]:
        """Get list of available workflows with metadata."""
        workflows = []
        for file_path in self.directories["workflows"].glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                workflows.append({
                    "id": file_path.stem,
                    "metadata": data.get("metadata", {}),
                    "path": str(file_path)
                })
            except Exception as e:
                self.logger.warning(f"Failed to read workflow {file_path}: {str(e)}")
                
        return workflows

    def clear_temp_files(self) -> None:
        """Clear temporary files."""
        try:
            for file_path in self.directories["temp"].glob("*"):
                if file_path.is_file():
                    file_path.unlink()
            self.logger.info("Cleared temporary files")
        except Exception as e:
            self.logger.error(f"Failed to clear temp files: {str(e)}")
            self.storage_error.emit(f"Failed to clear temp files: {str(e)}")