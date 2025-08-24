from PySide6 import QtWidgets
from widgets.installable_widget import InstallableWidget
from widgets.version_selector_dialog import VersionSelectorDialog
from widgets.version_manager_widget import VersionManagerWidget
from ..FlowLayout import FlowLayout

from apps.godot import Godot


class GameEngines(QtWidgets.QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.container = QtWidgets.QWidget()
        self.layout = FlowLayout()
        self.container.setLayout(self.layout)
        self.addWidget(self.container)

        self.godot_app = Godot()
        self.godot_widget = InstallableWidget(
            title="Godot",
            description="The Godot game engine.",
            installed=self.godot_app.is_installed,
            on_install=self._handle_godot_install,
            on_manage_versions=self._handle_godot_manage_versions,
            show_success_message=False,
        )
        self.godot_version_manager = VersionManagerWidget(
            self.godot_app, "Godot", parent=self
        )

        self.layout.addWidget(self.godot_widget)

    def _handle_godot_install(self):
        self._handle_app_install(self.godot_app, self.godot_widget, "Godot")

    def _handle_app_install(self, app, widget, app_name):
        """Universal app installation handler with version selection"""

        if app_name == "Godot":
            available_versions = (
                self.godot_version_manager._get_available_versions_cached()
            )
        else:
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
            active_version = app.active_version
            if active_version:
                widget.description_label.setText(
                    f"{current_description} (v{active_version})"
                )

            QtWidgets.QMessageBox.information(self, "Installation Complete", "Done!")
        else:
            raise Exception("Installation cancelled by user")

    def _handle_godot_manage_versions(self):
        self.godot_version_manager.show_manager()
