from typing import Dict, Any, List, Optional
import torch
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import logging
import json
import numpy as np
from .base_component import BaseComponent, ComponentMetadata

class OutputComponent(BaseComponent):
    """Component for visualizing and saving CNN results."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        
        # Initialize metadata with port information
        self.metadata = ComponentMetadata(
            id="output",
            name="Graph Output",
            description="Visualizes and saves CNN results",
            version="1.0.0",
            category="Output",
            input_ports={
                "predictions": {
                    "type": "tensor",
                    "description": "Model predictions"
                },
                "confidence": {
                    "type": "tensor",
                    "description": "Prediction confidence scores"
                },
                "filenames": {
                    "type": "list",
                    "description": "List of processed file names"
                }
            },
            output_ports={
                "confusion_matrix_path": {
                    "type": "str",
                    "description": "Path to confusion matrix plot"
                },
                "confidence_plot_path": {
                    "type": "str",
                    "description": "Path to confidence distribution plot"
                }
            }
        )
        
        # Set default configuration
        self.config.update({
            "output_path": "./output/graphs",
            "dpi": 100,
            "class_names": [
                "airplane", "automobile", "bird", "cat", "deer",
                "dog", "frog", "horse", "ship", "truck"
            ]  # Default classes matching CNN component
        })
        
        # Create output directory
        self.output_path = Path(self.config["output_path"])
        self.output_path.mkdir(parents=True, exist_ok=True)
        
    def get_required_inputs(self) -> List[str]:
        """Define required input ports."""
        return ["predictions", "confidence"]
        
    def validate_inputs(self) -> bool:
        """Validate input data."""
        try:
            if not super().validate_inputs():
                return False
                
            predictions = self.input_ports["predictions"]
            confidence = self.input_ports["confidence"]
            
            if not isinstance(predictions, torch.Tensor):
                raise ValueError("Predictions must be a torch.Tensor")
                
            if not isinstance(confidence, torch.Tensor):
                raise ValueError("Confidence scores must be a torch.Tensor")
                
            if predictions.size(0) != confidence.size(0):
                raise ValueError("Predictions and confidence must have same batch size")
                
            return True
            
        except Exception as e:
            self.set_error(f"Input validation failed: {str(e)}")
            return False
            
    def process(self) -> Dict[str, Any]:
        """Process and visualize the CNN results."""
        try:
            if not self.validate_inputs():
                return None
                
            self.status = "processing"
            self.progress = 0
            
            predictions = self.input_ports["predictions"]
            confidence = self.input_ports["confidence"]
            filenames = self.input_ports.get("filenames", [f"Image_{i}" for i in range(len(predictions))])
            
            # Create visualizations
            plots = {}
            
            # 1. Generate confusion matrix
            self.status = "Creating confusion matrix"
            self.progress = 25
            cm_path = self._create_confusion_matrix(predictions)
            plots["confusion_matrix"] = str(cm_path)
            self.output_ports["confusion_matrix_path"] = str(cm_path)
            
            # 2. Generate confidence distribution
            self.status = "Creating confidence distribution"
            self.progress = 50
            conf_path = self._create_confidence_plot(confidence)
            plots["confidence_plot"] = str(conf_path)
            self.output_ports["confidence_plot_path"] = str(conf_path)
            
            # 3. Save prediction results
            self.status = "Saving prediction results"
            self.progress = 75
            results_path = self._save_prediction_results(predictions, confidence, filenames)
            
            self.status = "completed"
            self.progress = 100
            
            return {
                "status": "success",
                "plots": plots,
                "results_file": str(results_path),
                "num_predictions": len(predictions)
            }
            
        except Exception as e:
            self.set_error(f"Processing failed: {str(e)}")
            return None
            
    def _create_confusion_matrix(self, predictions: torch.Tensor) -> Path:
        """Create and save confusion matrix plot."""
        plt.figure(figsize=(12, 10))
        pred_classes = predictions.argmax(dim=1).numpy()
        
        # Create confusion matrix
        cm = np.zeros((len(self.config["class_names"]), len(self.config["class_names"])))
        for i in range(len(predictions)):
            cm[0][pred_classes[i]] += 1  # Using 0 as true label since we don't have ground truth
            
        # Plot confusion matrix
        sns.heatmap(cm, annot=True, fmt="g", xticklabels=self.config["class_names"],
                   yticklabels=self.config["class_names"])
        plt.title("Prediction Distribution")
        plt.xlabel("Predicted Class")
        plt.ylabel("True Class")
        
        # Save plot
        output_path = self.output_path / "confusion_matrix.png"
        plt.savefig(output_path, dpi=self.config["dpi"], bbox_inches="tight")
        plt.close()
        
        return output_path
        
    def _create_confidence_plot(self, confidence: torch.Tensor) -> Path:
        """Create and save confidence distribution plot."""
        plt.figure(figsize=(10, 6))
        
        # Create confidence histogram
        plt.hist(confidence.numpy(), bins=20, range=(0, 1), alpha=0.75)
        plt.title("Prediction Confidence Distribution")
        plt.xlabel("Confidence Score")
        plt.ylabel("Number of Predictions")
        
        # Save plot
        output_path = self.output_path / "confidence_distribution.png"
        plt.savefig(output_path, dpi=self.config["dpi"], bbox_inches="tight")
        plt.close()
        
        return output_path
        
    def _save_prediction_results(self, predictions: torch.Tensor, 
                               confidence: torch.Tensor, 
                               filenames: List[str]) -> Path:
        """Save detailed prediction results."""
        output_path = self.output_path / "prediction_results.json"
        
        results = []
        pred_classes = predictions.argmax(dim=1)
        
        for i, (pred, conf, filename) in enumerate(zip(pred_classes, confidence, filenames)):
            results.append({
                "filename": filename,
                "predicted_class": self.config["class_names"][pred.item()],
                "confidence": float(conf)
            })
            
        with open(output_path, "w") as f:
            json.dump({"predictions": results}, f, indent=2)
            
        return output_path
        
    def cleanup(self):
        """Clean up resources and temporary files."""
        try:
            plt.close("all")  # Close any remaining plots
            super().cleanup()
        except Exception as e:
            self.logger.error(f"Cleanup failed: {str(e)}")

