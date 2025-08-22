from state_manager import state_manager, TEMP_PATH
from apps.Apps import NonManagedApp
import subprocess
import os
import httpx


class VSCodeApp(NonManagedApp):
    def __init__(self):
        self.app_name = "vscode"
        self.is_installed = state_manager.is_app_installed(self.app_name)

    def install(self):
        """Install VSCode (non-managed, just install)"""

        installer_url = (
            "https://update.code.visualstudio.com/latest/win32-x64-user/stable"
        )
        installer_path = os.path.join(TEMP_PATH, "VSCodeSetup.exe")

        with httpx.stream("GET", installer_url, follow_redirects=True) as response:
            response.raise_for_status()
            with open(installer_path, "wb") as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)

        subprocess.run([installer_path], check=True)
        state_manager.set_app_installed(self.app_name, True)
        self.is_installed = True
