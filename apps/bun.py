from state_manager import state_manager
from widgets.version_selector_dialog import VersionSelectorDialog
from shim_manager import shim_manager
import httpx
from state_manager import APPS_DIR, TEMP_PATH
import zipfile
import shutil

from apps.Apps import ManagedApp


class Bun(ManagedApp):
    path = APPS_DIR / "bun"

    def __init__(self):
        super().__init__("bun")

    def get_available_versions(self):
        """Get list of available Bun versions from GitHub releases"""
        response = httpx.get("https://api.github.com/repos/oven-sh/bun/releases").json()
        versions = []
        for release in response:
            if release.get("draft") or release.get("prerelease"):
                continue

            tag_name = release["tag_name"]
            version = (
                tag_name.replace("bun-", "")
                if tag_name.startswith("bun-")
                else tag_name
            )

            display_name = version
            if release == response[0]:
                display_name = f"{version} (Latest)"

            versions.append({"real_name": version, "display_name": display_name})

        return versions

    def install(self, version: str = None):
        """Install Bun with the specified version"""
        if version is None:
            available_versions = self.get_available_versions()
            version = VersionSelectorDialog.select_version("Bun", available_versions)
            if not version:
                print("Installation cancelled.")
                return

        current_installed_versions = self.list_installed_versions()
        if version in current_installed_versions:
            print(f"Bun {version} is already installed.")
            return

        print(f"Installing Bun {version}...")

        tag_name = f"bun-{version}" if not version.startswith("bun-") else version
        download_url = f"https://github.com/oven-sh/bun/releases/download/{tag_name}/bun-windows-x64.zip"

        filename = "bun-windows-x64.zip"
        install_path = self.path / version
        install_path.mkdir(parents=True, exist_ok=True)

        with httpx.stream("GET", download_url, follow_redirects=True) as response:
            if response.status_code == 200:
                with open(install_path / filename, "wb") as f:
                    for chunk in response.iter_bytes():
                        f.write(chunk)
            else:
                print(f"Failed to download Bun {version}: {response.status_code}")
                return

        with zipfile.ZipFile(install_path / filename, "r") as zip_ref:
            zip_ref.extractall(install_path)

        (install_path / filename).unlink(missing_ok=True)
        self._add_installed_version(version, str(install_path))

        if not self.active_version:
            self._set_active_version(version)
            self._save_state(
                installed=True, version=version, install_path=str(install_path)
            )

        print(f"Bun {version} installed successfully at {install_path}")
        if self.active_version == version:
            self._create_shims(version)

    def uninstall(self, version: str = None):
        """Uninstall Bun or specific version"""
        if version is None:
            print("Uninstalling all Bun versions...")
            self._remove_shims()
            for installed_version in list(self.installed_versions.keys()):
                self._uninstall_version(installed_version)
            from state_manager import state_manager

            state_manager.remove_app_completely(self.app_name)

            self._load_state()
            print("All Bun versions uninstalled successfully")
        else:
            if version not in self.installed_versions:
                print(f"Bun {version} is not installed.")
                return

            print(f"Uninstalling Bun {version}...")
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
                    from state_manager import state_manager

                    state_manager.remove_app_completely(self.app_name)
                    self._load_state()

            print(f"Bun {version} uninstalled successfully")

    def _uninstall_version(self, version: str):
        """Remove a specific version's files"""
        version_path = self.path / version
        if version_path.exists():
            shutil.rmtree(version_path, ignore_errors=True)

    def _create_shims(self, version: str):
        """Create PowerShell shims for Bun executables"""

        extracted_folder_name = "bun-windows-x64"
        shims_config = [
            {"executable_name": "bun.exe", "executable_subpath": extracted_folder_name},
        ]
        created_shims = shim_manager.create_multiple_shims(self.app_name, shims_config)
        print(
            f"Created {len(created_shims)} shims: {[shim.name for shim in created_shims]}"
        )
        from state_manager import APPS_DIR

        install_path = APPS_DIR / "bun" / version / extracted_folder_name
        print(f"Shims pointing to: {install_path}")
        if install_path.exists():
            print(f"✓ Path exists")
            bun_exe = install_path / "bun.exe"
            if bun_exe.exists():
                print(f"✓ bun.exe found")
            else:
                print(f"✗ bun.exe NOT found at {bun_exe}")
        else:
            print(f"✗ Path does NOT exist")

    def _remove_shims(self):
        """Remove PowerShell shims for Bun executables"""
        executable_names = ["bun"]
        removed_count = shim_manager.remove_multiple_shims(executable_names)
        print(f"Removed {removed_count} shims")

    def _update_shims_for_version(self, version: str):
        """Update shims to point to specific version"""
        self._remove_shims()
        self._create_shims(version)
