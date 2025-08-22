from state_manager import state_manager
from widgets.version_selector_dialog import VersionSelectorDialog
from shim_manager import shim_manager
from state_manager import APPS_DIR, TEMP_PATH


class NonManagedApp:
    def __init__(self, name, install_func):
        self.name = name
        self.install_func = install_func

    def install(self):
        return self.install_func()


class ManagedApp:
    def __init__(self, app_name: str):
        self.app_name = app_name
        self._load_state()

    def _load_state(self):
        """Load the app state from storage"""
        self.is_installed = state_manager.is_app_installed(self.app_name)
        self.version = state_manager.get_app_version(self.app_name)
        self.active_version = state_manager.get_app_active_version(self.app_name)
        self.installed_versions = state_manager.get_app_installed_versions(
            self.app_name
        )

    def _save_state(
        self, installed: bool, version: str = None, install_path: str = None
    ):
        """Save the app state to storage"""
        state_manager.set_app_installed(self.app_name, installed, version, install_path)
        self.is_installed = installed
        if version:
            self.version = version

    def _add_installed_version(self, version: str, install_path: str):
        """Add a version to the list of installed versions"""
        state_manager.add_app_version(self.app_name, version, install_path)
        self._load_state()

    def _remove_installed_version(self, version: str):
        """Remove a version from the list of installed versions"""
        state_manager.remove_app_version(self.app_name, version)
        self._load_state()

    def _set_active_version(self, version: str):
        """Set the active version and update shims"""
        if version not in self.installed_versions:
            raise ValueError(f"Version {version} is not installed")

        state_manager.set_app_active_version(self.app_name, version)
        self.active_version = version

        self._update_shims_for_version(version)

    def get_available_versions(self):
        """Get list of available versions for this app. Override in subclasses.
        Should return a list of dicts: { 'real_name': str, 'display_name': str }
        """
        raise NotImplementedError("get_available_versions method must be implemented.")

    def install(self, version: str = None):
        """Install the app with optional version specification"""
        raise NotImplementedError("Install method must be implemented.")

    def uninstall(self, version: str = None):
        """Uninstall the app or specific version"""
        raise NotImplementedError("Uninstall method must be implemented.")

    def switch_version(self, version: str):
        """Switch to a different installed version"""
        if not self.is_installed:
            raise ValueError(f"{self.app_name} is not installed")

        installed_version_keys = (
            list(self.installed_versions.keys()) if self.installed_versions else []
        )
        if version not in installed_version_keys:
            raise ValueError(f"Version {version} is not installed")

        self._set_active_version(version)
        print(f"Switched {self.app_name} to version {version}")

    def list_installed_versions(self):
        """List all installed versions"""
        installed_versions_dict = (
            self.installed_versions if self.installed_versions else {}
        )
        return list(installed_versions_dict.keys())

    def get_active_version(self):
        """Get the currently active version"""
        return self.active_version

    def _update_shims_for_version(self, version: str):
        """Update shims to point to specific version. Override in subclasses."""
        pass
