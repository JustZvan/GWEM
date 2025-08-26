from PySide6 import QtWidgets
from widgets.installable_widget import InstallableWidget
from ..FlowLayout import FlowLayout
from apps.vscode import VSCodeApp
from apps.Apps import NonManagedApp
from state_manager import state_manager, TEMP_PATH
import httpx
import subprocess
import os


class SublimeTextApp(NonManagedApp):
    def __init__(self):
        self.app_name = "sublimetext"
        self.is_installed = state_manager.is_app_installed(self.app_name)

    def install(self):
        """Install Sublime (non-managed, just install)"""

        installer_url = (
            "https://download.sublimetext.com/sublime_text_build_4200_x64_setup.exe"
        )
        installer_path = os.path.join(TEMP_PATH, "SublimeSetup.exe")

        with httpx.stream("GET", installer_url, follow_redirects=True) as response:
            response.raise_for_status()
            with open(installer_path, "wb") as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)

        subprocess.run([installer_path], check=True)
        state_manager.set_app_installed(self.app_name, True)
        self.is_installed = True


class CodeEditors(QtWidgets.QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.container = QtWidgets.QWidget()
        self.layout = FlowLayout()
        self.container.setLayout(self.layout)
        self.addWidget(self.container)

        vscode = VSCodeApp()

        vscode_widget = InstallableWidget(
            title="VS Code",
            description="Popular open-source code editor.",
            installed=False,
            on_install=vscode.install,
            is_managed=False,
        )

        sublime_text = SublimeTextApp()

        sublime_widget = InstallableWidget(
            title="Sublime Text",
            description="Fast and lightweight code editor",
            installed=False,
            on_install=sublime_text.install,
            is_managed=False,
        )

        self.layout.addWidget(vscode_widget)
        self.layout.addWidget(sublime_widget)
