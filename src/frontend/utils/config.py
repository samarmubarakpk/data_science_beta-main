import json
from pathlib import Path
from typing import Dict, Any, Optional
from src.frontend.utils.logger import get_logger

class ConfigManager:
    """Manage application configuration."""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self.logger = get_logger(__name__)
        self.config: Dict[str, Any] = self.load_config()
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load config: {str(e)}")
        return self._default_config()
        
    def save_config(self) -> bool:
        """Save current configuration to file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Failed to save config: {str(e)}")
            return False
            
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)
        
    def set(self, key: str, value: Any):
        """Set configuration value."""
        self.config[key] = value
        self.save_config()
        
    def _default_config(self) -> Dict[str, Any]:
        """Create default configuration."""
        return {
            "recent_files": [],
            "max_recent_files": 10,
            "auto_save": True,
            "auto_save_interval": 300,  # 5 minutes
            "theme": "light",
            "component_snap_to_grid": True,
            "grid_size": 20,
            "default_save_dir": str(Path.home()),
            "window": {
                "geometry": None,
                "state": None
            },
            "logging": {
                "level": "INFO",
                "file": "app.log"
            },
            "ui": {
                "show_grid": True,
                "show_port_labels": True,
                "show_component_labels": True
            },
            "components": {
                "default_spacing": 50,
                "connection_style": "bezier"  # or "straight"
            }
        }