# src/frontend/components/cnn_component.py
from sklearn import metrics
from sklearn.discriminant_analysis import StandardScaler
import torch
from src.frontend.components.base import WorkflowComponent
from PyQt5.QtCore import QPointF, Qt ,QThread
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush
import numpy as np
from typing import Dict, Any
import torch.nn as nn
from PyQt5.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QProgressBar ,QApplication


class TrainingProgressWindow(QDialog):
    """Popup window to show training progress."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Training Progress")
        self.setGeometry(200, 200, 400, 150)
        self.setModal(True)  # Make window modal
        
        layout = QVBoxLayout()
        
        # Progress label
        self.progress_label = QLabel("Training Progress: 0%")
        layout.addWidget(self.progress_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        layout.addWidget(self.progress_bar)
        
        # Metrics labels
        self.loss_label = QLabel("Loss: -")
        self.accuracy_label = QLabel("Accuracy: -")
        layout.addWidget(self.loss_label)
        layout.addWidget(self.accuracy_label)
        
        self.setLayout(layout)
    
    def update_progress(self, progress: float, loss: float = None, accuracy: float = None):
        """Update the progress and metrics display."""
        self.progress_bar.setValue(int(progress))
        self.progress_label.setText(f"Training Progress: {progress:.1f}%")
        if loss is not None:
            self.loss_label.setText(f"Loss: {loss:.4f}")
        if accuracy is not None:
            self.accuracy_label.setText(f"Accuracy: {accuracy:.4f}")

class CNNComponent(WorkflowComponent):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Component appearance
        self.title = "Deep Learning Model"
        self.color = QColor("#805ad5")
        self.width = 160
        self.height = 80
        
        # Add ports with proper spacing
        input_y = self.height * 0.3
        output_y = self.height * 0.3
        metrics_y = self.height * 0.7
        
        self.add_input_port("input", "data", input_y)
        self.add_output_port("output", "data", output_y)
        self.add_output_port("metrics", "metrics", metrics_y)
        
        # Initialize progress window
        self.progress_window = None
        
        # Add training state
        self._is_training = False

        
        # Enhanced properties with TabularNN support
        self.properties = {
            "architecture": {
                "type": "choice",
                "label": "Architecture",
                "value": {
                    "selected": "tabularnn",
                    "choices": ["tabularnn", "resnet18", "resnet34", "vgg16", "mobilenet"]
                },
                "description": "Neural network architecture"
            },
            "task_type": {
                "type": "choice",
                "label": "Task Type",
                "value": {
                    "selected": "multiclass_classification",
                    "choices": ["multiclass_classification"]
                },
                "description": "Type of learning task"
            },
            "target_column": {
                "type": "string",
                "label": "Target Column",
                "value": "",
                "description": "Column to predict"
            },
            "hidden_layers": {
                "type": "string",
                "label": "Hidden Layers",
                "value": "64,32,16",
                "description": "Comma-separated layer sizes"
            },
            "learning_rate": {
                "type": "number",
                "label": "Learning Rate",
                "value": 0.001,
                "description": "Model learning rate"
            },
            "batch_size": {
                "type": "integer",
                "label": "Batch Size",
                "value": 32,
                "description": "Training batch size"
            },
            "epochs": {
                "type": "integer",
                "label": "Epochs",
                "value": 50,
                "description": "Number of training epochs"
            }
        }
        
        self._training_progress = 0
        self._metrics = None
        self._model = None

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        print("CNNComponent: Starting execution...")

        try:
            data = inputs.get("input")
            if data is None:
                print("CNNComponent ERROR: No input data provided")
                raise ValueError("No input data provided")

            arch = self.properties["architecture"]["value"]["selected"]
            print(f"CNNComponent: Using architecture: {arch}")

            if arch == "tabularnn":
                print("CNNComponent: Starting TabularNN training...")
                return self._train_tabular(data)
            else:
                print("CNNComponent: Starting CNN training...")
                return {
                    "status": "success",
                    "metrics": {
                        "loss": metrics["loss"],
                        "accuracy": metrics.get("accuracy", []),
                        "confusion_matrix": (
                            self._compute_confusion_matrix() 
                            if hasattr(self, '_model') else None
                        )
                    },
                    "summary": {
                        "final_loss": metrics["loss"][-1],
                        "final_accuracy": (
                            metrics["accuracy"][-1] if "accuracy" in metrics else None
                        )
                    }
                }
        except Exception as e:
            print(f"CNNComponent ERROR in execute: {str(e)}")
            return {"status": "error", "error": str(e)}


    def _train_tabular(self, data):
        """Train TabularNN model on input data."""
        print("CNNComponent: Starting tabular data training...")
        try:
            # Get parameters first and validate
            target_col = self.properties["target_column"]["value"]
            if not target_col:
                print("CNNComponent: No target column specified")
                if self.progress_window:
                    self.progress_window.reject()
                    self.progress_window = None
                    
                # Show error message in UI
                QMessageBox.critical(
                    None,
                    "Training Error",
                    "Please select a target column before training, establish connection again",
                    QMessageBox.Ok
                )
                
                return {
                    "status": "error",
                    "error": "Please select a target column before training, establish connection again"
                }

            # Additional validation
            if target_col not in data.columns:
                error_msg = f"Target column '{target_col}' not found in data.\nAvailable columns: {', '.join(data.columns)}"
                print(f"CNNComponent: {error_msg}")
                
                # Show error message in UI
                QMessageBox.critical(
                    None,
                    "Training Error",
                    error_msg,
                    QMessageBox.Ok
                )
                
                return {
                    "status": "error",
                    "error": error_msg
                }
        
            import torch
            import torch.nn as nn
            from sklearn.preprocessing import StandardScaler, LabelEncoder
            import numpy as np
            
            # Create progress window and initialize metrics
            self.progress_window = TrainingProgressWindow()
            self.progress_window.show()
            self._is_training = True
            self._metrics = {"loss": [], "accuracy": []}  # Initialize empty metrics
            self._predictions = None
            self._true_labels = None
            
            try:
                # Get parameters
                target_col = self.properties["target_column"]["value"]
                task_type = self.properties["task_type"]["value"]["selected"]
                print(f"CNNComponent: Task type: {task_type}, Target column: {target_col}")
                    
                # Update progress window
                self.progress_window.update_progress(0, loss=None, accuracy=None)
                self.progress_window.progress_label.setText("Preparing data...")
                
                # Prepare data
                X = data.drop(columns=[target_col])
                y = data[target_col]
                print(f"CNNComponent: Data shape - X: {X.shape}, y: {y.shape}")
                
                # Encode target labels for classification
                label_encoder = None
                if task_type in ["binary_classification", "multiclass_classification"]:
                    self.progress_window.progress_label.setText("Encoding labels...")
                    label_encoder = LabelEncoder()
                    y = label_encoder.fit_transform(y)
                    print(f"CNNComponent: Encoded {len(label_encoder.classes_)} classes")
                
                # Scale features
                self.progress_window.progress_label.setText("Scaling features...")
                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(X)
                X_tensor = torch.FloatTensor(X_scaled)
                y_tensor = torch.FloatTensor(y)
                
                # Set up model
                input_dim = X.shape[1]
                if task_type == "binary_classification":
                    output_dim = 1
                    criterion = nn.BCELoss()
                    y_tensor = y_tensor.float()
                elif task_type == "multiclass_classification":
                    output_dim = len(np.unique(y))
                    criterion = nn.CrossEntropyLoss()
                    y_tensor = torch.LongTensor(y)
                else:  # regression
                    output_dim = 1
                    criterion = nn.MSELoss()
                
                # Build model
                self.progress_window.progress_label.setText("Building model...")
                layer_sizes = [int(s) for s in self.properties["hidden_layers"]["value"].split(",")]
                self._model = self._build_tabular_model(input_dim, layer_sizes, output_dim, task_type)
                
                # Training setup
                optimizer = torch.optim.Adam(
                    self._model.parameters(), 
                    lr=self.properties["learning_rate"]["value"]
                )
                epochs = self.properties["epochs"]["value"]
                metrics = {"loss": [], "accuracy": []}
                
                # Training loop
                self.progress_window.progress_label.setText("Training model...")
                for epoch in range(epochs):
                    self._model.train()
                    optimizer.zero_grad()
                    
                    # Forward pass
                    outputs = self._model(X_tensor)
                    loss = criterion(outputs, y_tensor)
                    
                    # Backward pass
                    loss.backward()
                    optimizer.step()
                    
                    # Calculate metrics
                    current_loss = loss.item()
                    current_accuracy = None
                    
                    if task_type != "regression":
                        with torch.no_grad():
                            if task_type == "binary_classification":
                                predicted = (outputs > 0.5).float()
                            else:  # multiclass_classification
                                _, predicted = outputs.max(1)
                            correct = (predicted == y_tensor).float().sum()
                            current_accuracy = (correct / len(y_tensor)).item()
                    
                    # Store metrics for each epoch
                    self._metrics["loss"].append(current_loss)
                    if current_accuracy is not None:
                        self._metrics["accuracy"].append(current_accuracy)
                    
                    # Print progress every 50 epochs
                    if epoch % 50 == 0:
                        print(f"CNNComponent: Epoch {epoch}/{epochs}")
                        print(f"Loss: {current_loss:.4f}")
                        if current_accuracy is not None:
                            print(f"Accuracy: {current_accuracy:.4f}")
                    
                    # Update progress window
                    progress = ((epoch + 1) / epochs) * 100
                    self.progress_window.update_progress(
                        progress,
                        loss=current_loss,
                        accuracy=current_accuracy
                    )
                    
                    # Force UI update
                    QApplication.processEvents()
                
                # After training, compute final predictions
                with torch.no_grad():
                    final_outputs = self._model(X_tensor)
                    if task_type == "multiclass_classification":
                        _, predictions = final_outputs.max(1)
                        self._predictions = predictions.numpy()
                    else:
                        self._predictions = (final_outputs > 0.5).float().numpy()
                    self._true_labels = y
                
                # Print final metrics summary
                print("\nCNNComponent: Training completed successfully")
                print(f"Total epochs recorded: {len(self._metrics['loss'])}")
                print(f"Final loss: {self._metrics['loss'][-1]:.4f}")
                if 'accuracy' in self._metrics:
                    print(f"Final accuracy: {self._metrics['accuracy'][-1]:.4f}")
                
                # Clean up
                self.progress_window.progress_label.setText("Training completed!")
                QThread.msleep(500)
                self.progress_window.accept()
                self.progress_window = None
                self._is_training = False
                
                return {
                    "status": "success",
                    "metrics": self._metrics,
                    "predictions": self._predictions,
                    "true_labels": self._true_labels,
                    "model": self._model,
                    "summary": {
                        "final_loss": self._metrics["loss"][-1],
                        "final_accuracy": self._metrics["accuracy"][-1] if "accuracy" in self._metrics else None
                    }
                }
                
            except Exception as e:
                print(f"CNNComponent ERROR in training: {str(e)}")
                if self.progress_window:
                    self.progress_window.reject()
                    self.progress_window = None
                self._is_training = False
                return {"status": "error", "error": str(e)}
                
        except Exception as e:
            print(f"CNNComponent ERROR in initialization: {str(e)}")
            self._is_training = False
            return {"status": "error", "error": str(e)}            
                



    def _build_tabular_model(self, input_dim, hidden_layers, output_dim, task_type):
        """Build PyTorch model for tabular data."""
        print(f"CNNComponent: Building model with input_dim: {input_dim}, output_dim: {output_dim}")
        try:
            layers = []
            prev_size = input_dim
            
            # Add hidden layers
            for size in hidden_layers:
                print(f"CNNComponent: Adding hidden layer with size: {size}")
                layers.extend([
                    nn.Linear(prev_size, size),
                    nn.ReLU(),
                    nn.BatchNorm1d(size),
                    nn.Dropout(0.2)
                ])
                prev_size = size
                
            # Add output layer
            print(f"CNNComponent: Adding output layer with size: {output_dim}")
            layers.append(nn.Linear(prev_size, output_dim))
            if task_type == "binary_classification":
                print("CNNComponent: Adding Sigmoid activation for binary classification")
                layers.append(nn.Sigmoid())
            elif task_type == "multiclass_classification":
                print("CNNComponent: Adding Softmax activation for multiclass classification")
                layers.append(nn.Softmax(dim=1))
                
            model = nn.Sequential(*layers)
            print("CNNComponent: Model built successfully")
            return model

        except Exception as e:
            print(f"CNNComponent ERROR in _build_tabular_model: {str(e)}")
            raise

    def _calculate_accuracy(self, outputs, targets):
        """Calculate accuracy for classification tasks."""
        try:
            with torch.no_grad():
                if outputs.shape[1] == 1:  # Binary classification
                    predicted = (outputs > 0.5).float()
                else:  # Multiclass classification
                    _, predicted = outputs.max(1)
                correct = (predicted == targets).float().sum()
                accuracy = correct / targets.size(0)
                return accuracy.item()
        except Exception as e:
            print(f"CNNComponent ERROR in _calculate_accuracy: {str(e)}")
            return 0.0

    
    def paint(self, painter: QPainter, option, widget=None):
        """Enhanced visual representation."""
        super().paint(painter, option, widget)
        
        # Draw model type and task
        arch = self.properties["architecture"]["value"]["selected"]
        if arch == "tabularnn":
            task = self.properties["task_type"]["value"]["selected"]
            painter.setPen(QPen(QColor("#1a202c")))  # Dark text color
            painter.drawText(10, 45, f"Model: TabularNN")
            painter.drawText(10, 60, f"Task: {task}")
        else:
            painter.setPen(QPen(QColor("#1a202c")))
            painter.drawText(10, 45, f"Model: {arch}")
        
        # Draw training status or metrics without background
        if self._is_training:
            painter.drawText(10, 75, "Training in progress...")
        elif hasattr(self, '_metrics') and self._metrics:
            metrics_text = ""
            if 'loss' in self._metrics:
                metrics_text += f"Loss: {self._metrics['loss'][-1]:.3f}"
            if 'accuracy' in self._metrics:
                metrics_text += f"  Acc: {self._metrics['accuracy'][-1]:.3f}"
            painter.drawText(10, 75, metrics_text)