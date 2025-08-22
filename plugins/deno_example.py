# Example Plugin - Deno Runtime
# This is an example plugin showing how to extend GWEM with new applications
# Copy this file to %APPDATA%/GWEM/plugins/ to use it

import sys
import os
from pathlib import Path

# The plugin manager will handle imports, but we need these for type hints
try:
    from state_manager import state_manager, APPS_DIR
    from widgets.version_selector_dialog import VersionSelectorDialog
    from shim_manager import shim_manager
    from apps.Apps import ManagedApp
    import httpx
    import zipfile
    import shutil
except ImportError as e:
    # This is expected when the plugin is being loaded
    pass


class Deno:
    """Example plugin: Deno JavaScript/TypeScript runtime"""

    display_name = "Deno"
    description = "A secure runtime for JavaScript and TypeScript"

    def __init__(self):
        # Import modules that should be available when the plugin is loaded
        global state_manager, APPS_DIR, VersionSelectorDialog, shim_manager, ManagedApp, httpx, zipfile, shutil

        from state_manager import state_manager, APPS_DIR
        from widgets.version_selector_dialog import VersionSelectorDialog
        from shim_manager import shim_manager
        from apps.Apps import ManagedApp
        import httpx
        import zipfile
        import shutil

        # Initialize as a ManagedApp
        self.app_name = "deno"
        self.path = APPS_DIR / "deno"
        self.is_installed = state_manager.is_app_installed(self.app_name)
        self.version = state_manager.get_app_version(self.app_name)
        self.active_version = state_manager.get_app_active_version(self.app_name)
        self.installed_versions = state_manager.get_app_installed_versions(
            self.app_name
        )

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
        state_manager.set_app_active_version(self.app_name, version)
        self.active_version = version
        self._update_shims_for_version(version)

    def list_installed_versions(self):
        """Get list of installed versions"""
        return list(self.installed_versions.keys())

    def get_available_versions(self):
        """Get list of available Deno versions from GitHub releases"""
        try:
            response = httpx.get("https://api.github.com/repos/denoland/deno/releases")
            response.raise_for_status()
            releases = response.json()

            versions = []
            for release in releases[:10]:  # Limit to first 10 releases
                if release.get("draft") or release.get("prerelease"):
                    continue

                tag_name = release["tag_name"]
                version = tag_name.lstrip("v")  # Remove 'v' prefix if present

                display_name = version
                if release == releases[0]:
                    display_name = f"{version} (Latest)"

                versions.append({"real_name": version, "display_name": display_name})

            return versions
        except Exception as e:
            print(f"Failed to fetch Deno versions: {e}")
            return []

    def install(self, version: str = None):
        """Install Deno with the specified version"""
        if version is None:
            available_versions = self.get_available_versions()
            if not available_versions:
                print("No versions available for installation.")
                return

            version = VersionSelectorDialog.select_version("Deno", available_versions)
            if not version:
                print("Installation cancelled.")
                return

        current_installed_versions = self.list_installed_versions()
        if version in current_installed_versions:
            print(f"Deno {version} is already installed.")
            return

        print(f"Installing Deno {version}...")

        # Deno GitHub release URL format
        download_url = f"https://github.com/denoland/deno/releases/download/v{version}/deno-x86_64-pc-windows-msvc.zip"

        filename = "deno-x86_64-pc-windows-msvc.zip"
        install_path = self.path / version
        install_path.mkdir(parents=True, exist_ok=True)

        try:
            with httpx.stream("GET", download_url, follow_redirects=True) as response:
                response.raise_for_status()
                with open(install_path / filename, "wb") as f:
                    for chunk in response.iter_bytes():
                        f.write(chunk)

            with zipfile.ZipFile(install_path / filename, "r") as zip_ref:
                zip_ref.extractall(install_path)

            (install_path / filename).unlink(missing_ok=True)
            self._add_installed_version(version, str(install_path))

            if not self.active_version:
                self._set_active_version(version)
                self._save_state(
                    installed=True, version=version, install_path=str(install_path)
                )

            print(f"Deno {version} installed successfully at {install_path}")
            if self.active_version == version:
                self._create_shims(version)

        except Exception as e:
            print(f"Failed to install Deno {version}: {e}")
            # Clean up partial installation
            if install_path.exists():
                shutil.rmtree(install_path, ignore_errors=True)

    def uninstall(self, version: str = None):
        """Uninstall Deno or specific version"""
        if version is None:
            print("Uninstalling all Deno versions...")
            self._remove_shims()
            for installed_version in list(self.installed_versions.keys()):
                self._uninstall_version(installed_version)

            state_manager.remove_app_completely(self.app_name)
            self._load_state()
            print("All Deno versions uninstalled successfully")
        else:
            if version not in self.installed_versions:
                print(f"Deno {version} is not installed.")
                return

            print(f"Uninstalling Deno {version}...")
            is_active_version = self.active_version == version
            self._uninstall_version(version)
            self._remove_installed_version(version)

            if is_active_version:
                remaining_versions = list(self.installed_versions.keys())
                if remaining_versions:
                    new_active = remaining_versions[0]
                    self._set_active_version(new_active)
                    print(f"Set {new_active} as the new active version")
                else:
                    self._remove_shims()
                    state_manager.remove_app_completely(self.app_name)
                    self._load_state()

            print(f"Deno {version} uninstalled successfully")

    def _uninstall_version(self, version: str):
        """Remove a specific version's files"""
        version_path = self.path / version
        if version_path.exists():
            shutil.rmtree(version_path, ignore_errors=True)

    def _create_shims(self, version: str):
        """Create PowerShell shims for Deno executable"""
        install_path = self.path / version
        shim_config = [
            {
                "executable_name": "deno.exe",
                "shim_name": "deno",
            }
        ]
        print(shim_config)
        created_shims = shim_manager.create_multiple_shims("deno", shim_config)
        if install_path.exists():
            print("✓ Path exists")
            deno_exe = install_path / "deno.exe"
            if deno_exe.exists():
                print("✓ deno.exe found")
            else:
                print(f"✗ deno.exe NOT found at {deno_exe}")
        else:
            print("✗ Path does NOT exist")

    def _remove_shims(self):
        """Remove PowerShell shims for Deno executable"""
        executable_names = ["deno"]
        removed_count = shim_manager.remove_multiple_shims(executable_names)
        print(f"Removed {removed_count} shims")

    def _update_shims_for_version(self, version: str):
        """Update shims to point to specific version"""
        self._remove_shims()
        self._create_shims(version)
