from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import torch
from torchvision import transforms
from PIL import Image
import logging
import os
from .base_component import BaseComponent, ComponentMetadata

# class InputComponent(BaseComponent):
#     """Component for handling image input and preprocessing."""
    
#     def __init__(self, config: Dict[str, Any] = None):
#         super().__init__(config)
        
#         # Initialize metadata with port information
#         self.metadata = ComponentMetadata(
#             id="input",
#             name="File Input",
#             description="Handles image input and preprocessing",
#             version="1.0.0",
#             category="Input",
#             input_ports={},  # No input ports needed
#             output_ports={
#                 "images": {
#                     "type": "tensor",
#                     "description": "Processed image batch"
#                 },
#                 "filenames": {
#                     "type": "list",
#                     "description": "List of processed file names"
#                 }
#             }
#         )
        
#         # Setup image transformation pipeline
#         self.transform = transforms.Compose([
#             transforms.Resize(256),
#             transforms.CenterCrop(224),
#             transforms.ToTensor(),
#             transforms.Normalize(
#                 mean=[0.485, 0.456, 0.406],
#                 std=[0.229, 0.224, 0.225]
#             )
#         ])
        
#         self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp'}
#         self.processed_files = []
        
#     def get_required_inputs(self) -> List[str]:
#         """No required inputs for input component."""
#         return []
        
#     def set_input_path(self, path: Union[str, Path]) -> bool:
#         """Set the input path and validate it."""
#         try:
#             input_path = Path(path)
#             if not input_path.exists():
#                 raise FileNotFoundError(f"Path does not exist: {input_path}")
                
#             if input_path.is_file() and input_path.suffix.lower() not in self.supported_formats:
#                 raise ValueError(f"Unsupported file format: {input_path.suffix}")
                
#             self.config["input_path"] = str(input_path)
#             self.status = "ready"
#             return True
            
#         except Exception as e:
#             self.set_error(f"Failed to set input path: {str(e)}")
#             return False
            
#     def process(self) -> Dict[str, Any]:
#         """Process input images and prepare them for the CNN."""
#         try:
#             if not self.config.get("input_path"):
#                 raise ValueError("Input path not configured")
                
#             input_path = Path(self.config["input_path"])
#             self.status = "processing"
#             self.progress = 0
            
#             # Get list of files to process
#             files_to_process = []
#             if input_path.is_file():
#                 if input_path.suffix.lower() in self.supported_formats:
#                     files_to_process.append(input_path)
#             else:
#                 files_to_process = [
#                     f for f in input_path.glob("*.*")
#                     if f.suffix.lower() in self.supported_formats
#                 ]
                
#             if not files_to_process:
#                 raise ValueError("No valid image files found")
                
#             # Process images
#             processed_images = []
#             processed_filenames = []
#             total_files = len(files_to_process)
            
#             for idx, img_path in enumerate(files_to_process, 1):
#                 try:
#                     # Update progress
#                     self.progress = (idx * 100) // total_files
                    
#                     # Load and process image
#                     image = Image.open(img_path).convert("RGB")
#                     transformed_image = self.transform(image)
#                     processed_images.append(transformed_image)
#                     processed_filenames.append(img_path.name)
                    
#                     # Update status
#                     self.status = f"Processing image {idx}/{total_files}"
                    
#                 except Exception as e:
#                     self.logger.warning(f"Failed to process image {img_path}: {str(e)}")
#                     continue
                    
#             if not processed_images:
#                 raise ValueError("No images were successfully processed")
                
#             # Stack images into batch
#             image_batch = torch.stack(processed_images)
            
#             # Set output ports
#             self.output_ports["images"] = image_batch
#             self.output_ports["filenames"] = processed_filenames
            
#             # Update status
#             self.status = "completed"
#             self.progress = 100
            
#             return {
#                 "status": "success",
#                 "num_processed": len(processed_images),
#                 "filenames": processed_filenames
#             }
            
#         except Exception as e:
#             self.set_error(f"Processing failed: {str(e)}")
#             return None
            
#     def supports_file(self, filename: str) -> bool:
#         """Check if a file is supported based on its extension."""
#         return Path(filename).suffix.lower() in self.supported_formats
        
#     def get_processed_files(self) -> List[str]:
#         """Get list of successfully processed files."""
#         return self.processed_files.copy()
        
#     def cleanup(self):
#         """Clean up resources."""
#         self.processed_files.clear()
#         self.output_ports["images"] = None
#         self.output_ports["filenames"] = None
#         super().cleanup()
# frontend/src/components/file_component.py
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

import pandas as pd
import numpy as np
from src.frontend.components.base import WorkflowComponent, Port

class FileComponent(WorkflowComponent):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.title = "File Input"
        self.color = QColor("#2563eb")
        self.data = None
        self.file_path = ""
        
        # Add output port
        self.add_output_port("data", "dataset", 40)
        
        # Add properties
        self.properties = {
            "file_path": {
                "type": "file",
                "value": "",
                "label": "File Path",
                "description": "Path to input file (CSV, Excel)"
            },
            "sheet_name": {
                "type": "string",
                "value": "Sheet1",
                "label": "Sheet Name",
                "description": "Sheet name for Excel files"
            }
        }

    def set_property(self, name: str, value: Any):
        super().set_property(name, value)
        if name == "file_path" and value:
            self.load_data(value)

    def load_data(self, file_path: str):
        try:
            if file_path.endswith('.csv'):
                self.data = pd.read_csv(file_path)
            elif file_path.endswith(('.xls', '.xlsx')):
                self.data = pd.read_excel(file_path, sheet_name=self.properties["sheet_name"]["value"])
            self.file_path = file_path
            self.update()
        except Exception as e:
            print(f"Error loading file: {str(e)}")

    def get_data(self):
        return self.data
