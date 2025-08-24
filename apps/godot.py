from state_manager import state_manager
from widgets.version_selector_dialog import VersionSelectorDialog
from shim_manager import shim_manager
import httpx
from state_manager import APPS_DIR, TEMP_PATH
import zipfile
import shutil
import re
from pathlib import Path


import os
from apps.Apps import ManagedApp
from shortcut_manager import shortcut_manager


class Godot(ManagedApp):
    path = APPS_DIR / "godot"

    def __init__(self):
        super().__init__("godot")

    def get_available_versions(self):
        response = httpx.get(
            "https://api.github.com/repos/godotengine/godot/releases",
            follow_redirects=True,
        )

        if response.status_code == 200:
            releases = response.json()

            sorted_releases = sorted(
                releases, key=lambda r: r["tag_name"], reverse=True
            )
            return [release["tag_name"] for release in sorted_releases]

        return []

    def uninstall(self, version: str = None):
        if version is None:
            print("Uninstalling all Godot versions...")
            shortcut_manager.remove_shortcut("Godot")
            for installed_version in list(self.installed_versions.keys()):
                version_path = self.path
                if os.path.exists(version_path):
                    shutil.rmtree(version_path, ignore_errors=True)
                self._remove_installed_version(installed_version)
            state_manager.remove_app_completely(self.app_name)
            self._load_state()
            print("All Godot versions uninstalled successfully")
        else:
            if version not in self.installed_versions:
                print(f"Godot {version} is not installed.")
                return
            print(f"Uninstalling Godot {version}...")
            version_path = self.path
            if os.path.exists(version_path):
                shutil.rmtree(version_path, ignore_errors=True)
            self._remove_installed_version(version)
            shortcut_manager.remove_shortcut("Godot")
            is_active_version = self.active_version == version
            if is_active_version:
                remaining_versions = list(self.installed_versions.keys())
                if remaining_versions:
                    new_active = remaining_versions[0]
                    self._set_active_version(new_active)
                    print(f"Set {new_active} as the new active version")
                else:
                    state_manager.remove_app_completely(self.app_name)
                    self._load_state()
            print(f"Godot {version} uninstalled successfully")

    def install(self, version: str = None):
        import os

        if not version:
            version = state_manager.get("godot_version")
        if not version:
            available = self.get_available_versions()
            if not available:
                print("No Godot versions found!")
                return
            version = available[0]

        print(f"Installing Godot version: {version}")
        response = httpx.get(
            f"https://api.github.com/repos/godotengine/godot/releases/tags/{version}",
            follow_redirects=True,
        )
        if response.status_code != 200:
            print(f"Failed to fetch release info for {version}: {response.status_code}")
            return
        release = response.json()
        assets = release.get("assets", [])

        version_clean = version.replace("-stable", "")

        pattern = re.compile(
            r"Godot_v[\d\.]+(_[\d]+)?_win64\.exe\.zip|Godot_v[\d\.]+-stable_win64\.exe\.zip"
        )
        asset_url = None
        asset_name = None
        for asset in assets:
            if pattern.match(asset["name"]):
                asset_url = asset["browser_download_url"]
                asset_name = asset["name"]
                break
        if not asset_url:
            print("No matching Godot asset found for Windows 64-bit.")
            return
        print(f"Downloading asset: {asset_name}")
        self.download_and_extract(asset_url, asset_name, version)

    def download_and_extract(self, url: str, asset_name: str, version: str):
        headers = {"Accept": "application/octet-stream"}
        print(url)
        response = httpx.get(url, headers=headers, follow_redirects=True)
        if response.status_code != 200:
            print(f"Failed to download asset: {response.status_code}")
            return
        zip_path = TEMP_PATH / asset_name
        with open(zip_path, "wb") as f:
            f.write(response.content)

        os.makedirs(self.path / version, exist_ok=True)

        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(self.path / version)

            print(f"Extracted Godot to {self.path / version}")

            godot_exe = None

            for file in os.listdir(self.path / version):
                if file.lower().startswith("godot") and file.lower().endswith(".exe"):
                    godot_exe = file
                    break
            if godot_exe:
                version_str = version

                self._add_installed_version(version_str, str(self.path / version))

                if not self.active_version:
                    self._set_active_version(version_str)
                    self._save_state(
                        installed=True,
                        version=version_str,
                        install_path=str(self.path / version),
                    )

                shortcut_manager.create_shortcut(
                    app_name="godot",
                    executable_name=godot_exe,
                    shortcut_name="Godot",
                    executable_subpath="",
                    description="Godot Engine",
                    icon_path=str(self.path / version / godot_exe),
                    working_directory=str(self.path / version),
                    arguments="",
                )
            else:
                print("Godot executable not found after extraction.")
        except Exception as e:
            print(f"Failed to extract zip: {e}")
        zip_path.unlink()

    def _get_shortcut_configs(self):
        """Get shortcut configurations for Godot"""
        if not self.active_version:
            return []

        version_to_use = self.active_version
        version_path = self.path / version_to_use

        if not version_path.exists() and not version_to_use.endswith("-stable"):
            version_to_use = f"{version_to_use}-stable"
            version_path = self.path / version_to_use

        if not version_path.exists():
            print(f"Version path not found: {version_path}")
            return []

        godot_exe = None
        for file in os.listdir(version_path):
            if file.lower().startswith("godot") and file.lower().endswith(".exe"):
                godot_exe = file
                break

        if godot_exe:
            return [
                {
                    "executable_name": godot_exe,
                    "shortcut_name": "Godot",
                    "executable_subpath": "",
                    "description": "Godot Engine",
                    "icon_path": str(version_path / godot_exe),
                    "working_directory": str(version_path),
                    "arguments": "",
                }
            ]
        return []

    def _update_shortcuts_for_version(self, version: str):
        """Recreate shortcuts for the specific version"""
        super()._update_shortcuts_for_version(version)

    def _update_shims_for_version(self, version: str):
        self._update_shortcuts_for_version(version)

    def fix_version_mismatch(self):
        """Fix version mismatch between stored version and actual folder names"""
        print("Checking for Godot version mismatches...")

        versions_to_update = {}
        for stored_version, install_path in self.installed_versions.items():
            expected_path = self.path / stored_version
            actual_path = Path(install_path)

            if expected_path != actual_path:
                actual_folder = actual_path.name
                print(
                    f"Found mismatch: stored '{stored_version}' -> actual folder '{actual_folder}'"
                )
                versions_to_update[stored_version] = actual_folder

        if versions_to_update:
            for old_version, new_version in versions_to_update.items():
                install_path = self.installed_versions[old_version]

                self._remove_installed_version(old_version)
                self._add_installed_version(new_version, install_path)

                if self.active_version == old_version:
                    self._set_active_version(new_version)
                    print(
                        f"Updated active version from '{old_version}' to '{new_version}'"
                    )

            shortcut_manager.remove_shortcut("Godot")
            configs = self._get_shortcut_configs()
            if configs:
                config = configs[0]
                shortcut_manager.create_shortcut(
                    app_name="godot",
                    executable_name=config["executable_name"],
                    shortcut_name=config["shortcut_name"],
                    executable_subpath=config["executable_subpath"],
                    description=config["description"],
                    icon_path=config["icon_path"],
                    working_directory=config["working_directory"],
                    arguments=config.get("arguments", ""),
                )
                print("Recreated Godot shortcut with correct version")

            self._load_state()
            print("Version mismatch fixed!")
