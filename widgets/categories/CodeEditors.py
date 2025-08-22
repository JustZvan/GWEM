from PySide6 import QtWidgets
from widgets.installable_widget import InstallableWidget
from ..FlowLayout import FlowLayout
from apps.vscode import VSCodeApp


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
        self.layout.addWidget(vscode_widget)
