from apps.Apps import ManagedApp
from state_manager import APPS_DIR, TEMP_PATH
from shim_manager import shim_manager
import httpx
import re
from pathlib import Path
import zipfile
import shutil


class Php(ManagedApp):
    path = APPS_DIR / "php"

    def __init__(self):
        super().__init__("php")

    def parse_versions(self, sb):
        regex = r'<A HREF="([a-zA-Z0-9./-]+)">([a-zA-Z0-9./-]+)</A>'
        matches = re.findall(regex, sb)
        versions = []

        for url, name in matches:
            name: str = name

            if name and name.startswith("php-devel-pack-"):
                continue
            if name and name.startswith("php-debug-pack-"):
                continue
            if name and name.startswith("php-test-pack-"):
                continue
            if name and "src" in name:
                continue
            if name and not name.endswith(".zip"):
                continue
            if name and not ("nts" in name or "NTS" in name):
                continue
            if name and not "x64" in name:
                continue

            version_name = name.split("-")[1]

            versions.append({"real_name": name, "display_name": version_name})

        return versions[::-1]

    def get_available_versions(self):
        resp = httpx.get("https://windows.php.net/downloads/releases/archives/")

        versions = self.parse_versions(resp.text)

        return versions

    def install(self, url: str):
        version = url.split("-")[1]
        print(url)

        install_path = self.path / version

        install_path.mkdir(parents=True, exist_ok=True)
        print("b")

        with httpx.stream(
            "GET", f"https://windows.php.net/downloads/releases/archives/{url}"
        ) as response:
            if response.status_code == 200:
                with open(install_path / f"php_{version}.zip", "wb") as f:
                    for chunk in response.iter_bytes():
                        f.write(chunk)
            else:
                print(f"Failed to download PHP {version}: {response.status_code}")
                return

        with zipfile.ZipFile(install_path / f"php_{version}.zip", "r") as zip_ref:
            zip_ref.extractall(install_path)

        (install_path / f"php_{version}.zip").unlink(True)

        self._add_installed_version(version, str(install_path))

        if not self.active_version:
            self._set_active_version(version)
            self._save_state(
                installed=True, version=version, install_path=str(install_path)
            )

        if self.active_version == version:
            self._create_shims(version)

    def _create_shims(self, version: str):
        """Create PowerShell shims for PHP executables"""
        shims_config = [
            {
                "executable_name": "php.exe",
                "executable_subpath": "",
                "shim_name": "php",
            },
        ]
        created_shims = shim_manager.create_multiple_shims(self.app_name, shims_config)
        print(
            f"Created {len(created_shims)} shims: {[shim.name for shim in created_shims]}"
        )

    def _remove_shims(self):
        """Remove PowerShell shims for PHP executables"""
        executable_names = ["php"]
        removed_count = shim_manager.remove_multiple_shims(executable_names)
        print(f"Removed {removed_count} shims")

    def _update_shims_for_version(self, version: str):
        """Update shims to point to specific version"""

        self._remove_shims()

        self._create_shims(version)

    def uninstall(self, version: str = None):
        """Uninstall PHP or specific version"""
        if version is None:
            print("Uninstalling all PHP versions...")
            self._remove_shims()
            for installed_version in list(self.installed_versions.keys()):
                self._uninstall_version(installed_version)
            from state_manager import state_manager

            state_manager.remove_app_completely(self.app_name)

            self._load_state()
            print("All PHP versions uninstalled successfully")
        else:
            if version not in self.installed_versions:
                print(f"PHP {version} is not installed.")
                return

            print(f"Uninstalling PHP {version}...")
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

            print(f"PHP {version} uninstalled successfully")

    def _uninstall_version(self, version: str):
        """Remove a specific version's files"""
        version_path = self.path / version
        if version_path.exists():
            shutil.rmtree(version_path, ignore_errors=True)
