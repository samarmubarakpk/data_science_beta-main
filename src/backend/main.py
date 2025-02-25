import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QSettings
import logging

# Add project root to Python path
sys.path.append(str(Path(__file__).parent))

# Import managers
from src.core.workflow_engine import WorkflowEngine
from src.core.component_manager import ComponentManager
from src.core.data_manager import DataManager

# Import UI components
from src.ui.main_window import MainWindow
from src.utils.logger import setup_logger

class Application:
    """Main application class."""
    
    def __init__(self):
        # Initialize logging
        setup_logger()
        self.logger = logging.getLogger(__name__)
        
        # Initialize settings
        self.settings = QSettings('YourCompany', 'DataMiningApp')
        
        # Initialize core components
        self.data_manager = DataManager(
            base_path=self.settings.value('data_path', './data')
        )
        self.component_manager = ComponentManager()
        self.workflow_engine = WorkflowEngine(self.data_manager)
        
        # Register available components with the manager
        self._register_components()
        
    def _register_components(self):
        """Register all available components."""
        try:
            # Register input component
            from src.components.input_component import InputComponent
            self.component_manager.register_component(
                "input",
                InputComponent,
                {
                    "icon": ":/icons/input.png",
                    "category": "Input"
                }
            )
            
            # Register CNN component
            from src.components.cnn_component import CNNComponent
            self.component_manager.register_component(
                "cnn",
                CNNComponent,
                {
                    "icon": ":/icons/cnn.png",
                    "category": "Processing"
                }
            )
            
            # Register output component
            from src.components.output_component import OutputComponent
            self.component_manager.register_component(
                "output",
                OutputComponent,
                {
                    "icon": ":/icons/output.png",
                    "category": "Output"
                }
            )
            
            self.logger.info("Successfully registered all components")
            
        except Exception as e:
            self.logger.error(f"Failed to register components: {str(e)}")
            raise
            
    def run(self):
        """Run the application."""
        try:
            # Create QApplication instance
            app = QApplication(sys.argv)
            
            # Enable high DPI support
            app.setAttribute(Qt.AA_EnableHighDpiScaling)
            app.setAttribute(Qt.AA_UseHighDpiPixmaps)
            
            # Create main window
            window = MainWindow(
                component_manager=self.component_manager,
                workflow_engine=self.workflow_engine,
                data_manager=self.data_manager
            )
            
            # Set window preferences
            window.setMinimumSize(1024, 768)
            window.show()
            
            # Run event loop
            return app.exec_()
            
        except Exception as e:
            self.logger.error(f"Application failed to start: {str(e)}")
            return 1
            
    def cleanup(self):
        """Clean up resources before exit."""
        try:
            # Save settings
            self.settings.sync()
            
            # Clean up managers
            self.workflow_engine.cleanup()
            self.data_manager.cleanup()
            
            self.logger.info("Application cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {str(e)}")
            
def main():
    """Application entry point."""
    try:
        # Create and run application
        app = Application()
        
        # Handle cleanup on exit
        result = app.run()
        app.cleanup()
        
        sys.exit(result)
        
    except Exception as e:
        logging.error(f"Application error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()