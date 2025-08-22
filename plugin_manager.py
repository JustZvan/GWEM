import os
import sys
import importlib.util
from pathlib import Path
from typing import Dict, List, Any
from state_manager import PLUGINS_DIR

# Import the base classes so plugins can inherit from them
import sys

sys.path.append(str(Path(__file__).parent))
from apps.Apps import ManagedApp, NonManagedApp


class PluginManager:
    def __init__(self):
        self.plugins = {}
        self.plugin_instances = {}
        self._ensure_plugins_directory()
        self._load_plugins()

    def _ensure_plugins_directory(self):
        """Ensure the plugins directory exists"""
        PLUGINS_DIR.mkdir(parents=True, exist_ok=True)

    def _load_plugins(self):
        """Load all Python plugins from the plugins directory"""
        if not PLUGINS_DIR.exists():
            return

        # Add plugins directory to Python path
        if str(PLUGINS_DIR) not in sys.path:
            sys.path.insert(0, str(PLUGINS_DIR))

        # Find all Python files in the plugins directory
        for plugin_file in PLUGINS_DIR.glob("*.py"):
            if plugin_file.name.startswith("__"):
                continue  # Skip __init__.py and __pycache__ files

            try:
                self._load_plugin(plugin_file)
            except Exception as e:
                print(f"Warning: Failed to load plugin {plugin_file.name}: {e}")

    def _load_plugin(self, plugin_file: Path):
        """Load a single plugin file"""
        plugin_name = plugin_file.stem

        # Load the module dynamically
        spec = importlib.util.spec_from_file_location(plugin_name, plugin_file)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load plugin spec for {plugin_name}")

        module = importlib.util.module_from_spec(spec)

        # Add the current working directory to sys.path temporarily for plugin imports
        original_path = sys.path.copy()
        try:
            # Add the main GWEM directory to path so plugins can import GWEM modules
            gwem_dir = Path(__file__).parent
            if str(gwem_dir) not in sys.path:
                sys.path.insert(0, str(gwem_dir))

            spec.loader.exec_module(module)
        finally:
            # Restore original path
            sys.path = original_path

        # Look for classes that might be app classes
        plugin_classes = []
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and attr_name
                not in ["ManagedApp", "NonManagedApp"]  # Exclude the base classes
                and not attr_name.startswith("_")
            ):  # Exclude private classes

                # Check if it has the methods/attributes we expect for an app
                has_install = hasattr(attr, "install") and callable(
                    getattr(attr, "install")
                )
                has_app_attributes = (
                    hasattr(attr, "display_name")
                    or hasattr(attr, "app_name")
                    or hasattr(attr, "description")
                )

                if has_install and has_app_attributes:
                    plugin_classes.append(attr)

        if plugin_classes:
            self.plugins[plugin_name] = {
                "module": module,
                "classes": plugin_classes,
                "file_path": plugin_file,
            }
            print(
                f"Loaded plugin: {plugin_name} with {len(plugin_classes)} app class(es)"
            )
        else:
            print(f"Warning: No valid app classes found in plugin {plugin_name}")

    def get_plugin_apps(self) -> Dict[str, List[Any]]:
        """Get all plugin app instances, organized by plugin name"""
        plugin_apps = {}

        for plugin_name, plugin_info in self.plugins.items():
            apps = []
            for app_class in plugin_info["classes"]:
                try:
                    # Create instance of the app class
                    app_instance = app_class()
                    apps.append(app_instance)
                except Exception as e:
                    print(
                        f"Warning: Failed to instantiate {app_class.__name__} from plugin {plugin_name}: {e}"
                    )

            if apps:
                plugin_apps[plugin_name] = apps

        return plugin_apps

    def get_all_plugin_app_instances(self) -> List[Any]:
        """Get all plugin app instances as a flat list"""
        all_apps = []
        plugin_apps = self.get_plugin_apps()

        for plugin_name, apps in plugin_apps.items():
            all_apps.extend(apps)

        return all_apps

    def reload_plugins(self):
        """Reload all plugins"""
        # Clear existing plugins
        self.plugins.clear()
        self.plugin_instances.clear()

        # Remove plugins directory from sys.path if it was added
        if str(PLUGINS_DIR) in sys.path:
            sys.path.remove(str(PLUGINS_DIR))

        # Reload plugins
        self._load_plugins()

    def get_plugin_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all loaded plugins"""
        info = {}
        for plugin_name, plugin_data in self.plugins.items():
            info[plugin_name] = {
                "file_path": str(plugin_data["file_path"]),
                "classes": [cls.__name__ for cls in plugin_data["classes"]],
                "class_count": len(plugin_data["classes"]),
            }
        return info


# Global plugin manager instance
plugin_manager = PluginManager()
