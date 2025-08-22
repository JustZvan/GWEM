import json
import os
from pathlib import Path
from typing import Dict, Any

BASEDIR = Path(os.environ.get("APPDATA", "")) / "GWEM"
APPS_DIR = BASEDIR / "apps"
TEMP_PATH = BASEDIR / "temp"
PATH_DIR = BASEDIR / "path"


class StateManager:
    def __init__(self):
        self.appdata_path = BASEDIR
        self.apps_file = self.appdata_path / "apps.json"
        self.preferences_file = self.appdata_path / "preferences.json"
        self._ensure_directories()
        self._apps_state = self._load_apps_state()
        self._preferences = self._load_preferences()

    def _ensure_directories(self):
        """Ensure the GWEM directory exists in APPDATA"""
        self.appdata_path.mkdir(parents=True, exist_ok=True)

    def _load_apps_state(self) -> Dict[str, Any]:
        """Load apps state from the apps.json file"""
        if self.apps_file.exists():
            try:
                with open(self.apps_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load apps state file: {e}")
                return {}
        return {}

    def _load_preferences(self) -> Dict[str, Any]:
        """Load preferences from the preferences.json file, creating default if it doesn't exist"""
        default_preferences = {
            "style": "Fusion",
            "created_date": self._get_current_timestamp(),
            "last_modified": self._get_current_timestamp(),
        }

        if self.preferences_file.exists():
            try:
                with open(self.preferences_file, "r", encoding="utf-8") as f:
                    preferences = json.load(f)

                    for key, value in default_preferences.items():
                        if key not in preferences:
                            preferences[key] = value
                    return preferences
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load preferences file: {e}")

        self._save_preferences(default_preferences)
        return default_preferences

    def _save_apps_state(self):
        """Save current apps state to the apps.json file"""
        try:
            with open(self.apps_file, "w", encoding="utf-8") as f:
                json.dump(self._apps_state, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error: Could not save apps state file: {e}")

    def _save_preferences(self, preferences: Dict[str, Any] = None):
        """Save preferences to the preferences.json file"""
        if preferences is None:
            preferences = self._preferences

        preferences["last_modified"] = self._get_current_timestamp()

        try:
            with open(self.preferences_file, "w", encoding="utf-8") as f:
                json.dump(preferences, f, indent=2, ensure_ascii=False)
            self._preferences = preferences
        except IOError as e:
            print(f"Error: Could not save preferences file: {e}")

    def get_app_state(self, app_name: str) -> Dict[str, Any]:
        """Get the state for a specific app"""
        return self._apps_state.get(app_name, {})

    def set_app_state(self, app_name: str, state: Dict[str, Any]):
        """Set the state for a specific app"""
        self._apps_state[app_name] = state
        self._save_apps_state()

    def is_app_installed(self, app_name: str) -> bool:
        """Check if an app is marked as installed"""
        app_state = self.get_app_state(app_name)
        return app_state.get("installed", False)

    def set_app_installed(
        self,
        app_name: str,
        installed: bool,
        version: str = None,
        install_path: str = None,
    ):
        """Mark an app as installed or uninstalled"""
        app_state = self.get_app_state(app_name)
        app_state["installed"] = installed

        if installed:
            if version:
                app_state["version"] = version
            if install_path:
                app_state["install_path"] = install_path
            app_state["install_date"] = self._get_current_timestamp()
        else:
            app_state.pop("install_path", None)
            app_state["uninstall_date"] = self._get_current_timestamp()

        self.set_app_state(app_name, app_state)

    def get_app_version(self, app_name: str) -> str:
        """Get the installed version of an app"""
        app_state = self.get_app_state(app_name)
        return app_state.get("version", "")

    def get_installed_apps(self) -> Dict[str, Dict[str, Any]]:
        """Get all installed apps and their state"""
        return {
            name: state
            for name, state in self._apps_state.items()
            if state.get("installed", False)
        }

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a preference value"""
        return self._preferences.get(key, default)

    def set_preference(self, key: str, value: Any):
        """Set a preference value"""
        self._preferences[key] = value
        self._save_preferences()

    def get_style(self) -> str:
        """Get the UI style preference"""
        return self.get_preference("style", "Fusion")

    def set_style(self, style: str):
        """Set the UI style preference"""
        if style in ["Fusion", "Windows"]:
            self.set_preference("style", style)
        else:
            raise ValueError("Style must be 'Fusion' or 'Windows'")

    def get_all_preferences(self) -> Dict[str, Any]:
        """Get all preferences"""
        return self._preferences.copy()

    def _get_current_timestamp(self) -> str:
        """Get current timestamp as ISO string"""
        from datetime import datetime

        return datetime.now().isoformat()

    def get_app_active_version(self, app_name: str) -> str:
        """Get the active version of an app"""
        app_state = self.get_app_state(app_name)
        return app_state.get("active_version", "")

    def set_app_active_version(self, app_name: str, version: str):
        """Set the active version of an app"""
        app_state = self.get_app_state(app_name)
        app_state["active_version"] = version
        app_state["last_version_change"] = self._get_current_timestamp()
        self.set_app_state(app_name, app_state)

    def get_app_installed_versions(self, app_name: str) -> Dict[str, str]:
        """Get all installed versions of an app with their install paths"""
        app_state = self.get_app_state(app_name)
        return app_state.get("installed_versions", {})

    def add_app_version(self, app_name: str, version: str, install_path: str):
        """Add a new installed version"""
        app_state = self.get_app_state(app_name)
        if "installed_versions" not in app_state:
            app_state["installed_versions"] = {}
        app_state["installed_versions"][version] = install_path
        app_state["last_install"] = self._get_current_timestamp()
        self.set_app_state(app_name, app_state)

    def remove_app_version(self, app_name: str, version: str):
        """Remove an installed version"""
        app_state = self.get_app_state(app_name)
        if (
            "installed_versions" in app_state
            and version in app_state["installed_versions"]
        ):
            del app_state["installed_versions"][version]
            app_state["last_uninstall"] = self._get_current_timestamp()
            self.set_app_state(app_name, app_state)

    def remove_app_completely(self, app_name: str):
        """Completely remove an app from the state"""
        if app_name in self._apps_state:
            del self._apps_state[app_name]
            self._save_apps_state()


state_manager = StateManager()
