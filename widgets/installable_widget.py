from PySide6 import QtWidgets, QtCore


class InstallableWidget(QtWidgets.QWidget):
    def __init__(
        self,
        title,
        description,
        installed=False,
        on_install=None,
        on_uninstall=None,
        on_manage_versions=None,
        parent=None,
        is_managed=True,
    ):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout()
        self.title_label = QtWidgets.QLabel(title)
        self.description_label = QtWidgets.QLabel(description)
        self.installed = installed
        self.on_install = on_install
        self.on_uninstall = on_uninstall
        self.on_manage_versions = on_manage_versions
        self.is_managed = is_managed

        self.install_button = QtWidgets.QPushButton()
        self.update_button_text()
        self.install_button.clicked.connect(self.handle_button)

        self.manage_versions_button = QtWidgets.QPushButton("Manage Versions")
        self.manage_versions_button.clicked.connect(self.handle_manage_versions)
        self.manage_versions_button.setVisible(
            self.installed and self.on_manage_versions is not None
        )

        layout.addWidget(self.title_label)
        layout.addWidget(self.description_label)
        layout.addWidget(self.install_button)
        layout.addWidget(self.manage_versions_button)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Minimum
        )
        self.setMaximumWidth(200)
        self.setMaximumHeight(self.sizeHint().height())

    def handle_button(self):
        if not self.installed:
            if self.on_install:
                self.on_install()
            self.installed = True
        else:
            if self.on_uninstall:
                self.on_uninstall()
                self.installed = False
        self.update_button_text()
        self.update_manage_versions_button()

    def handle_manage_versions(self):
        if self.on_manage_versions:
            self.on_manage_versions()

    def update_button_text(self):
        if not self.is_managed:
            self.install_button.setText("Launch Installer")
            return

        if self.installed and not self.on_uninstall:
            self.install_button.setVisible(False)
        else:
            self.install_button.setVisible(True)
            if self.installed:
                self.install_button.setText("Uninstall")
            else:
                self.install_button.setText("Install")

    def update_manage_versions_button(self):
        """Update the visibility of the manage versions button"""
        self.manage_versions_button.setVisible(
            self.installed and self.on_manage_versions is not None
        )
