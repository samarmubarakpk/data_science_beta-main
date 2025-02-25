# src/frontend/components/graph_component.py
from .base import WorkflowComponent
from PyQt5.QtCore import QPointF, Qt 
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
from typing import Dict, Any
import matplotlib.pyplot as plt
import pandas as pd
import io
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
from PyQt5.QtCore import QRectF
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QMessageBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class PlotWindow(QDialog):
    """Separate window for displaying plots."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Data Visualization")
        self.setGeometry(100, 100, 600, 400)
        
        layout = QVBoxLayout()
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

class GraphComponent(WorkflowComponent):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.title = "Graph Output"
        self.color = QColor("#3182ce")
        self.width = 120
        self.height = 80
        
        # Add input port
        port_y = self.height * 0.5
        self.add_input_port("input", "data", port_y)
        
        self.plot_window = None
        self._current_data = None
        
        # Updated properties with ML visualization options
        self.properties = {
            "graph_type": {
                "type": "choice",
                "label": "Graph Type",
                "value": {
                    "selected": "training_loss",
                    "choices": [
                        "training_loss",
                        "training_accuracy",
                        "confusion_matrix",
                        # "line",
                        # "bar",
                        # "scatter",
                        # "histogram"
                    ]
                }
            },
            "title": {
                "type": "string",
                "label": "Title",
                "value": ""
            },
            "x_column": {
                "type": "string",
                "label": "X Column",
                "value": ""
            },
            "y_column": {
                "type": "string",
                "label": "Y Column",
                "value": ""
            }
        }

    def execute(self, inputs: Dict[str, Any] = None) -> Dict[str, Any]:
        print("GraphComponent: Execute called")
        try:
            if not inputs or 'input' not in inputs:
                QMessageBox.warning(
                    None,
                    "Visualization Error",
                    "No data available for visualization.\nPlease ensure that:\n1. Model is trained\n2. Connection is properly established",
                    QMessageBox.Ok
                )
                return {"status": "error", "error": "No input data"}

            self._current_data = inputs['input']
            print(f"GraphComponent: Received input type: {type(self._current_data)}")

            # Create and show plot window
            self._create_plot(self._current_data)
            return {"status": "success"}

        except Exception as e:
            print(f"GraphComponent ERROR: {str(e)}")
            return {"status": "error", "error": str(e)}


    def set_property(self, name: str, value: Any):
        """Update properties and refresh plot if needed."""
        super().set_property(name, value)
        
        # If changing graph type and we have data, update the plot
        if name == "graph_type" and self._current_data is not None:
            print(f"GraphComponent: Updating visualization to {value}")
            self._create_plot(self._current_data)

    def _create_plot(self, data):
        try:
            print("GraphComponent: Creating plot...")
            
            # Create plot window if it doesn't exist
            if not self.plot_window:
                self.plot_window = PlotWindow()
                self.plot_window.setWindowTitle("Data Visualization")
            
            # Clear the current plot
            self.plot_window.figure.clear()
            ax = self.plot_window.figure.add_subplot(111)
            
            graph_type = self.properties["graph_type"]["value"]["selected"]
            
            if not data:
                ax.text(0.5, 0.5, 
                    'No data available.\nPlease train the model first.',
                    ha='center', va='center', fontsize=12)
                self.plot_window.canvas.draw()
                self.plot_window.show()
                self.plot_window.raise_()
                return

            # Check if metrics exist
            if "metrics" not in data or data["metrics"] is None:
                QMessageBox.warning(
                    None,
                    "Visualization Error",
                    "No training metrics available.\nPlease train the model first.",
                    QMessageBox.Ok
                )
                return

            metrics = data["metrics"]
            
            if graph_type == "training_loss":
                if "loss" in metrics and metrics["loss"]:
                    losses = metrics["loss"]
                    epochs = list(range(1, len(losses) + 1))
                    ax.plot(epochs, losses, 'b-', linewidth=2)
                    ax.set_title('Training Loss Over Time')
                    ax.set_xlabel('Epoch')
                    ax.set_ylabel('Loss')
                    ax.grid(True)
                    min_loss, max_loss = min(losses), max(losses)
                    padding = (max_loss - min_loss) * 0.1
                    ax.set_ylim(min_loss - padding, max_loss + padding)
                else:
                    ax.text(0.5, 0.5, 'No loss data available', ha='center', va='center')

            elif graph_type == "training_accuracy":
                if "accuracy" in metrics and metrics["accuracy"]:
                    accuracies = metrics["accuracy"]
                    epochs = list(range(1, len(accuracies) + 1))
                    ax.plot(epochs, accuracies, 'g-', linewidth=2)
                    ax.set_title('Training Accuracy Over Time')
                    ax.set_xlabel('Epoch')
                    ax.set_ylabel('Accuracy')
                    ax.grid(True)
                    ax.set_ylim(-0.05, 1.05)
                else:
                    ax.text(0.5, 0.5, 'No accuracy data available', ha='center', va='center')

            elif graph_type == "confusion_matrix":
                if ("predictions" in data and "true_labels" in data and 
                    data["predictions"] is not None and data["true_labels"] is not None):
                    from sklearn.metrics import confusion_matrix
                    import seaborn as sns
                    print("GraphComponent: Creating confusion matrix")
                    cm = confusion_matrix(data["true_labels"], data["predictions"])
                    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax)
                    ax.set_title('Confusion Matrix')
                    ax.set_xlabel('Predicted Label')
                    ax.set_ylabel('True Label')
                else:
                    ax.text(0.5, 0.5, 'Missing data for confusion matrix', ha='center', va='center')

            # Update the plot
            self.plot_window.canvas.draw()
            self.plot_window.show()
            self.plot_window.raise_()
            print("GraphComponent: Plot updated successfully")

        except Exception as e:
            print(f"GraphComponent ERROR in _create_plot: {str(e)}")
            QMessageBox.critical(
                None,
                "Visualization Error",
                f"Error creating plot: {str(e)}",
                QMessageBox.Ok
            )

    def paint(self, painter: QPainter, option, widget=None):
        """Simplified paint method - just shows component status."""
        super().paint(painter, option, widget)
        status_text = "Plot Window Open" if self.plot_window else "No Plot"
        painter.drawText(self.boundingRect().adjusted(10, 30, -10, -10), 
                        Qt.AlignCenter, status_text)
        

    def set_property(self, name: str, value: Any):
        """Handle property changes and update plot."""
        print(f"GraphComponent: Setting property {name} to {value}")
        super().set_property(name, value)
        if self._current_data is not None:
            self._create_plot(self._current_data)