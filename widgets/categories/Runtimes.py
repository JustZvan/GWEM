from PySide6 import QtWidgets
from widgets.installable_widget import InstallableWidget
from widgets.version_selector_dialog import VersionSelectorDialog
from widgets.version_manager_widget import VersionManagerWidget
from ..FlowLayout import FlowLayout


class Runtimes(QtWidgets.QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.container = QtWidgets.QWidget()
        self.layout = FlowLayout()
        self.container.setLayout(self.layout)
        self.addWidget(self.container)

        from apps.nodejs import NodeJS
        from apps.bun import Bun
        from apps.go import Golang

        self.nodejs_app = NodeJS()
        self.bun_app = Bun()
        self.golang_app = Golang()

        self.nodejs_widget = InstallableWidget(
            title="Node.js",
            description="The bulky JavaScript runtime.",
            installed=self.nodejs_app.is_installed,
            on_install=self._handle_nodejs_install,
            on_manage_versions=self._handle_nodejs_manage_versions,
            show_success_message=False,  # Disable default success message for managed apps
        )

        self.bun_widget = InstallableWidget(
            title="Bun",
            description="The fast JavaScript runtime.",
            installed=self.bun_app.is_installed,
            on_install=self._handle_bun_install,
            on_manage_versions=self._handle_bun_manage_versions,
            show_success_message=False,  # Disable default success message for managed apps
        )

        self.golang_widget = InstallableWidget(
            title="Go",
            description="The Go programming language.",
            installed=self.golang_app.is_installed,
            on_install=self._handle_golang_install,
            on_manage_versions=self._handle_golang_manage_versions,
            show_success_message=False,  # Disable default success message for managed apps
        )

        self.nodejs_version_manager = VersionManagerWidget(
            self.nodejs_app, "Node.js", parent=self
        )

        self.bun_version_manager = VersionManagerWidget(
            self.bun_app, "Bun", parent=self
        )

        self.golang_version_manager = VersionManagerWidget(
            self.golang_app, "Go", parent=self
        )

        self.layout.addWidget(self.nodejs_widget)
        self.layout.addWidget(self.bun_widget)
        self.layout.addWidget(self.golang_widget)

    def _handle_nodejs_install(self):
        """Handle Node.js installation with version selection"""
        self._handle_app_install(self.nodejs_app, self.nodejs_widget, "Node.js")

    def _handle_nodejs_uninstall(self):
        """Handle Node.js uninstall and sync widget state"""
        self._handle_app_uninstall(
            self.nodejs_app, self.nodejs_widget, "The bulky JavaScript runtime."
        )

    def _handle_nodejs_manage_versions(self):
        """Show the Node.js version manager dialog"""
        self.nodejs_version_manager.show_manager()

    def _handle_bun_install(self):
        """Handle Bun installation with version selection"""
        self._handle_app_install(self.bun_app, self.bun_widget, "Bun")

    def _handle_bun_uninstall(self):
        """Handle Bun uninstall and sync widget state"""
        self._handle_app_uninstall(
            self.bun_app, self.bun_widget, "The fast JavaScript runtime."
        )

    def _handle_bun_manage_versions(self):
        """Show the Bun version manager dialog"""
        self.bun_version_manager.show_manager()

    def _handle_golang_install(self):
        """Handle Go installation with version selection"""
        self._handle_app_install(self.golang_app, self.golang_widget, "Go")

    def _handle_golang_uninstall(self):
        """Handle Go uninstall and sync widget state"""
        self._handle_app_uninstall(
            self.golang_app, self.golang_widget, "The Go programming language."
        )

    def _handle_golang_manage_versions(self):
        """Show the Go version manager dialog"""
        self.golang_version_manager.show_manager()

    def _handle_app_install(self, app, widget, app_name):
        """Universal app installation handler with version selection"""
        available_versions = app.get_available_versions()
        selected_version = VersionSelectorDialog.select_version(
            app_name, available_versions, parent=self
        )

        if selected_version:
            app.install(selected_version)
            widget.installed = app.is_installed
            widget.update_manage_versions_button()
            current_description = widget.description_label.text()

            if " (v" in current_description:
                current_description = current_description.split(" (v")[0]
            active_version = app.get_active_version()
            if active_version:
                widget.description_label.setText(
                    f"{current_description} (v{active_version})"
                )

            # Show success message for managed apps
            QtWidgets.QMessageBox.information(self, "Installation Complete", "Done!")
        else:
            # User cancelled the version selection
            raise Exception("Installation cancelled by user")

    def _handle_app_uninstall(self, app, widget, original_description):
        """Universal app uninstall handler"""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm Uninstall",
            f"Are you sure you want to uninstall all versions of {app.app_name}?",
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            app.uninstall()
            widget.installed = app.is_installed
            widget.update_manage_versions_button()
            widget.description_label.setText(original_description)
