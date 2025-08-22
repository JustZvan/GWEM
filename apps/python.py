from sys import version
from state_manager import state_manager
from widgets.version_selector_dialog import VersionSelectorDialog
from shim_manager import shim_manager
import httpx
from state_manager import APPS_DIR, TEMP_PATH
import zipfile
import shutil
import json

from apps.Apps import ManagedApp


class Python(ManagedApp):
    path = APPS_DIR / "python"

    def __init__(self):
        super().__init__("python")

    def get_available_versions(self):
        """Get available versions of Python"""
        responseLegacy = httpx.get(
            "https://www.python.org/ftp/python/index-windows-legacy.json"
        )
        response = httpx.get("https://www.python.org/ftp/python/index-windows.json")
        responseRecent = httpx.get(
            "https://www.python.org/ftp/python/index-windows-recent.json"
        )

        data = json.loads(response.text)
        dataLegacy = json.loads(responseLegacy.text)
        dataRecent = json.loads(responseRecent.text)

        versions = []

        for version in dataLegacy["versions"]:
            if version["sort-version"] in versions:
                continue

            versions.append(version["sort-version"])

        for version in data["versions"]:
            if version["sort-version"] in versions:
                continue

            versions.append(version["sort-version"])

        for version in dataRecent["versions"]:
            if version["sort-version"] in versions:
                continue

            versions.append(version["sort-version"])

        # sort versions
        versions.sort(
            key=lambda x: [int(part) if part.isdigit() else 0 for part in x.split(".")],
            reverse=True,
        )

        return versions

    def install(self, version):
        print(version)

        import re

        match = re.match(
            r"^(\d+\.\d+\.\d+)(.*)$", version
        )  # this regex was made by gpt 4.1
        if match:
            base_version = match.group(1)
            suffix = match.group(2)
        else:
            base_version = version
            suffix = ""

        url = f"https://www.python.org/ftp/python/{base_version}/python-{version}-embed-amd64.zip"

        install_path = self.path / version
        filename = f"python-{version}-embed-amd64.zip"

        install_path.mkdir(parents=True, exist_ok=True)

        with httpx.stream("GET", url) as response:
            if response.status_code == 200:
                with open(install_path / filename, "wb") as f:
                    for chunk in response.iter_bytes():
                        f.write(chunk)
            else:
                print(f"Failed to download Python {version}: {response.status_code}")
                return

        with zipfile.ZipFile(install_path / filename, "r") as zip_ref:
            zip_ref.extractall(install_path)

        shim_manager.create_multiple_shims(
            "python",
            [
                {
                    "executable_name": "python.exe",
                    "executable_subpath": version,
                    "shim_name": "python",
                },
                {
                    "executable_name": "pythonw.exe",
                    "executable_subpath": version,
                    "shim_name": "pythonw",
                },
            ],
        )

        (install_path / filename).unlink(missing_ok=True)
        self._add_installed_version(version, str(install_path))

        if not self.active_version:
            self._set_active_version(version)
            self._save_state(
                installed=True, version=version, install_path=str(install_path)
            )


if __name__ == "__main__":
    python_app = Python()
    print(python_app.get_available_versions())
