# backend/src/components/cnn_component.py
from typing import Dict, Any, Optional, List
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import models, transforms
import torch.nn.functional as F
from pathlib import Path
import logging

from .base_component import BaseComponent, ComponentMetadata

class CNNComponent(BaseComponent):
    """Component for CNN-based image classification using pre-trained ResNet18."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        
        # Initialize metadata with port information
        self.metadata = ComponentMetadata(
            id="cnn_classifier",
            name="CNN Classifier",
            description="Image classification using pre-trained ResNet18",
            version="1.0.0",
            category="Processing",
            input_ports={
                "images": {
                    "type": "tensor",
                    "description": "Batch of images (B, C, H, W)"
                }
            },
            output_ports={
                "predictions": {
                    "type": "tensor",
                    "description": "Class predictions"
                },
                "confidence": {
                    "type": "tensor",
                    "description": "Prediction confidence scores"
                }
            }
        )
        
        # Setup model and device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.class_names = None
        self._initialize_model()
        
    def _initialize_model(self):
        """Initialize the pre-trained ResNet18 model."""
        try:
            # Load pre-trained ResNet18
            self.model = models.resnet18(pretrained=True)
            self.model = self.model.to(self.device)
            self.model.eval()  # Set to evaluation mode
            
            # Load ImageNet class names
            self.class_names = [
                "airplane", "automobile", "bird", "cat", "deer",
                "dog", "frog", "horse", "ship", "truck"
            ]  # Simplified class list for example
            
            self.status = "ready"
            
        except Exception as e:
            self.set_error(f"Failed to initialize model: {str(e)}")
            
    def get_required_inputs(self) -> List[str]:
        """Define required input ports."""
        return ["images"]
        
    def validate_inputs(self) -> bool:
        """Validate input tensor format."""
        try:
            if not super().validate_inputs():
                return False
                
            images = self.input_ports["images"]
            if not isinstance(images, torch.Tensor):
                raise ValueError("Images must be a torch.Tensor")
                
            if images.dim() != 4:
                raise ValueError("Images must be 4-dimensional (batch, channels, height, width)")
                
            if images.size(1) != 3:
                raise ValueError("Images must have 3 channels (RGB)")
                
            return True
            
        except Exception as e:
            self.set_error(f"Input validation failed: {str(e)}")
            return False
            
    def process(self) -> Dict[str, Any]:
        """Process images through the CNN model."""
        try:
            self.status = "processing"
            self.progress = 0
            
            # Validate inputs
            if not self.validate_inputs():
                return None
                
            # Get input images
            images = self.input_ports["images"].to(self.device)
            batch_size = images.size(0)
            
            # Process in batches if needed
            with torch.no_grad():
                # Forward pass
                outputs = self.model(images)
                
                # Get predictions and confidence scores
                probabilities = F.softmax(outputs, dim=1)
                confidence, predictions = torch.max(probabilities, dim=1)
                
                # Store outputs
                self.output_ports["predictions"] = predictions.cpu()
                self.output_ports["confidence"] = confidence.cpu()
                
                # Calculate progress
                self.progress = 100
                
            self.status = "completed"
            
            # Return results
            return {
                "status": "success",
                "predictions": [self.class_names[pred.item()] for pred in predictions],
                "confidence": confidence.tolist(),
                "num_processed": batch_size
            }
            
        except Exception as e:
            self.set_error(f"Processing failed: {str(e)}")
            return None
            
    def cleanup(self):
        """Clean up GPU memory and resources."""
        try:
            if self.model is not None:
                self.model.cpu()
                del self.model
                self.model = None
            torch.cuda.empty_cache()
            super().cleanup()
        except Exception as e:
            self.logger.error(f"Cleanup failed: {str(e)}")