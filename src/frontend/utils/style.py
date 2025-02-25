# frontend/src/utils/style.py
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt
from typing import Dict, Any

def set_dark_theme(app) -> None:
    """Apply dark theme to the application."""
    palette = QPalette()
    
    # Base colors
    palette.setColor(QPalette.Window, QColor("#1a1a1a"))
    palette.setColor(QPalette.WindowText, QColor("#ffffff"))
    palette.setColor(QPalette.Base, QColor("#2d2d2d"))
    palette.setColor(QPalette.AlternateBase, QColor("#353535"))
    palette.setColor(QPalette.PlaceholderText, QColor("#8a8a8a"))
    
    # Text colors
    palette.setColor(QPalette.Text, QColor("#ffffff"))
    palette.setColor(QPalette.BrightText, QColor("#ffffff"))
    
    # Button colors
    palette.setColor(QPalette.Button, QColor("#353535"))
    palette.setColor(QPalette.ButtonText, QColor("#ffffff"))
    
    # Link colors
    palette.setColor(QPalette.Link, QColor("#3d8ec9"))
    palette.setColor(QPalette.LinkVisited, QColor("#287399"))
    
    # Selection colors
    palette.setColor(QPalette.Highlight, QColor("#2d5c76"))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    
    # Tooltip colors
    palette.setColor(QPalette.ToolTipBase, QColor("#353535"))
    palette.setColor(QPalette.ToolTipText, QColor("#ffffff"))
    
    app.setPalette(palette)
    apply_dark_stylesheet(app)

def set_light_theme(app) -> None:
    """Apply light theme to the application."""
    palette = QPalette()
    
    # Base colors
    palette.setColor(QPalette.Window, QColor("#f5f5f5"))
    palette.setColor(QPalette.WindowText, QColor("#000000"))
    palette.setColor(QPalette.Base, QColor("#ffffff"))
    palette.setColor(QPalette.AlternateBase, QColor("#f7f7f7"))
    palette.setColor(QPalette.PlaceholderText, QColor("#7f7f7f"))
    
    # Text colors
    palette.setColor(QPalette.Text, QColor("#000000"))
    palette.setColor(QPalette.BrightText, QColor("#ffffff"))
    
    # Button colors
    palette.setColor(QPalette.Button, QColor("#e0e0e0"))
    palette.setColor(QPalette.ButtonText, QColor("#000000"))
    
    # Link colors
    palette.setColor(QPalette.Link, QColor("#0066cc"))
    palette.setColor(QPalette.LinkVisited, QColor("#004c99"))
    
    # Selection colors
    palette.setColor(QPalette.Highlight, QColor("#308cc6"))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    
    # Tooltip colors
    palette.setColor(QPalette.ToolTipBase, QColor("#ffffff"))
    palette.setColor(QPalette.ToolTipText, QColor("#000000"))
    
    app.setPalette(palette)
    apply_light_stylesheet(app)

def apply_stylesheet(app) -> None:
    """Apply base stylesheet to the application."""
    app.setStyleSheet("""
        /* Main Window */
        QMainWindow {
            background-color: palette(window);
        }
        
        /* Dock Widgets */
        QDockWidget {
            border: 1px solid palette(dark);
            titlebar-close-icon: url(close.png);
        }
        
        QDockWidget::title {
            background: palette(alternate-base);
            padding: 6px;
        }
        
        /* Tool Bar */
        QToolBar {
            border: none;
            background: palette(window);
            spacing: 6px;
            padding: 3px;
        }
        
        QToolButton {
            border: 1px solid transparent;
            border-radius: 4px;
            padding: 4px;
            background: transparent;
        }
        
        QToolButton:hover {
            background-color: palette(alternate-base);
            border: 1px solid palette(mid);
        }
        
        QToolButton:pressed {
            background-color: palette(dark);
        }
        
        /* Menu Bar */
        QMenuBar {
            background-color: palette(window);
            border-bottom: 1px solid palette(dark);
        }
        
        QMenuBar::item {
            padding: 4px 8px;
            background: transparent;
        }
        
        QMenuBar::item:selected {
            background-color: palette(highlight);
            color: palette(highlighted-text);
        }
        
        /* Status Bar */
        QStatusBar {
            background: palette(window);
            border-top: 1px solid palette(dark);
        }
        
        /* Scroll Areas */
        QScrollArea {
            border: none;
            background: transparent;
        }
        
        QScrollBar:vertical {
            border: none;
            background: palette(base);
            width: 12px;
            margin: 0px;
        }
        
        QScrollBar::handle:vertical {
            background: palette(button);
            border-radius: 6px;
            min-height: 20px;
            margin: 2px;
        }
        
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        /* Graphics View */
        QGraphicsView {
            border: none;
            selection-background-color: palette(highlight);
        }
    """)

def apply_dark_stylesheet(app) -> None:
    """Apply dark theme specific styles."""
    additional_styles = """
        /* Dark theme specific styles */
        QWidget {
            outline: none;
        }
        
        QToolTip {
            color: palette(tooltip-text);
            background-color: palette(tooltip-base);
            border: 1px solid palette(highlight);
        }
    """
    app.setStyleSheet(app.styleSheet() + additional_styles)

def apply_light_stylesheet(app) -> None:
    """Apply light theme specific styles."""
    additional_styles = """
        /* Light theme specific styles */
        QWidget {
            outline: none;
        }
        
        QToolTip {
            color: palette(tooltip-text);
            background-color: palette(tooltip-base);
            border: 1px solid palette(mid);
        }
    """
    app.setStyleSheet(app.styleSheet() + additional_styles)

def get_theme_colors(theme: str = "light") -> Dict[str, str]:
    """Get color palette for specified theme."""
    if theme == "dark":
        return {
            "background": "#1a1a1a",
            "foreground": "#ffffff",
            "primary": "#3d8ec9",
            "secondary": "#2d5c76",
            "success": "#28a745",
            "warning": "#ffc107",
            "error": "#dc3545",
            "border": "#353535"
        }
    else:
        return {
            "background": "#ffffff",
            "foreground": "#000000",
            "primary": "#0066cc",
            "secondary": "#308cc6",
            "success": "#28a745",
            "warning": "#ffc107",
            "error": "#dc3545",
            "border": "#e0e0e0"
        }