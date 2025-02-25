class ComponentManager:
    def __init__(self):
        self.components = {}
        
    def register_component(self, component_class):
        """Register a new component type."""
        self.components[component_class.__name__] = component_class
        
    def create_component(self, component_type):
        """Create a new component instance."""
        if component_type in self.components:
            return self.components[component_type]()
        return None