# main.py
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from src.frontend.ui.main_window import MainWindow

class Application(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        
        # Create main window
        self.main_window = MainWindow()
        self.main_window.show()

def main():
    # Enable high DPI support
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    # Create and run application
    app = Application(sys.argv)
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())