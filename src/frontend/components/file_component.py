from .base import WorkflowComponent
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
from PyQt5.QtWidgets import QFileDialog , QMessageBox
import pandas as pd
import json
from typing import Dict, Any


class FileComponent(WorkflowComponent):
    """Component for handling file input with support for multiple file types."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.title = "File Input"
        self.color = QColor("#48bb78")
        self.width = 120
        self._status = "ready"
        self._error = None 
        # Add output port
        port_y = self.height * 0.5
        self.add_output_port("output", "data", port_y)
        
        # Define file properties with enhanced options
        self.properties = {
            "file_path": {
                "type": "file",
                "label": "Input File",
                "value": "",
                "description": "Select input data file"
            },
            "file_type": {
                "type": "choice",
                "label": "File Type",
                "value": {
                    "selected": "csv",
                    "choices": ["csv", "excel", "json", "txt"]
                },
                "description": "Type of input file"
            },
            "has_header": {
                "type": "boolean",
                "label": "Has Header",
                "value": True,
                "description": "First row contains column names"
            },
            "delimiter": {
                "type": "choice",
                "label": "Delimiter",
                "value": {
                    "selected": ",",
                    "choices": [",", ";", "\t", "|"]
                },
                "description": "Column separator character"
            }
        }
        
        self._cached_data = None

    # In file_component.py
    def process(self, inputs=None):
        """Process the file input."""
        try:
            file_path = self.properties["file_path"]["value"]
            if not file_path:
                return None
                
            # Read file based on type
            file_type = self.properties["file_type"]["value"]["selected"]
            if file_type == "csv":
                return pd.read_csv(file_path)
            elif file_type == "excel":
                return pd.read_excel(file_path)
            # ... handle other file types ...
            
        except Exception as e:
            self.logger.error(f"Failed to process file: {str(e)}")
            return None

    def get_output(self):
        """Return the processed data."""
        return self.process()  

        
    def execute(self, inputs: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute file reading operation."""
        try:
            file_path = self.properties["file_path"]["value"]
            if not file_path:
                # Show UI warning when no file is selected
                QMessageBox.warning(
                    None,
                    "Input Required",
                    "Please add data to File Component before making connections.\n\nSteps:\n1. Select File Component\n2. Click 'Browse' in Properties panel\n3. Choose your data file\n4. And re-establish connection",
                    QMessageBox.Ok
                )
                return {
                    "status": "error",
                    "error": "No file selected"
                }
                
            print(f"FileComponent: Reading file from {file_path}")
            file_type = self.properties["file_type"]["value"]["selected"]
            has_header = self.properties["has_header"]["value"]
            delimiter = self.properties["delimiter"]["value"]["selected"]
            
            try:
                # Read file based on type
                if file_type == "csv":
                    data = pd.read_csv(
                        file_path,
                        header=0 if has_header else None,
                        delimiter=delimiter
                    )
                elif file_type == "excel":
                    data = pd.read_excel(
                        file_path,
                        header=0 if has_header else None
                    )
                elif file_type == "json":
                    with open(file_path, 'r') as f:
                        data = pd.DataFrame(json.load(f))
                else:
                    with open(file_path, 'r') as f:
                        data = pd.DataFrame([line.strip().split(delimiter) for line in f])
                        
                self._cached_data = data
                print(f"FileComponent: Successfully read data with shape: {data.shape}")
                print(f"FileComponent: Columns: {data.columns.tolist()}")
                
                return {
                    "output": data,
                    "status": "success",
                    "summary": {
                        "rows": len(data),
                        "columns": len(data.columns),
                        "file_type": file_type
                    }
                }
                
            except Exception as e:
                QMessageBox.critical(
                    None,
                    "File Error",
                    f"Error reading file:\n{str(e)}",
                    QMessageBox.Ok
                )
                return {
                    "status": "error",
                    "error": str(e)
                }
                
        except Exception as e:
            print(f"FileComponent ERROR: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
            
    def _read_file(self, file_path: str) -> pd.DataFrame:
        """Read file based on type with proper error handling."""
        file_type = self.properties["file_type"]["value"]["selected"]
        has_header = self.properties["has_header"]["value"]
        delimiter = self.properties["delimiter"]["value"]["selected"]
        
        try:
            if file_type == "csv":
                return pd.read_csv(file_path, 
                                 header=0 if has_header else None,
                                 delimiter=delimiter)
            elif file_type == "excel":
                return pd.read_excel(file_path,
                                   header=0 if has_header else None)
            # ... handle other file types ...
            
        except Exception as e:
            raise ValueError(f"Failed to read {file_type} file: {str(e)}")