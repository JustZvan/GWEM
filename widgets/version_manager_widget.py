from PySide6 import QtWidgets, QtCore
from typing import Dict, Any, Callable, Optional
from widgets.version_selector_dialog import VersionSelectorDialog


class VersionManagerWidget(QtWidgets.QDialog):
    """Dialog window for managing multiple versions of an application"""

    def __init__(self, app_instance, app_name: str, parent=None):
        super().__init__(parent)
        self.app_instance = app_instance
        self.app_name = app_name
        self.setWindowTitle(f"{app_name} Version Manager")
        self.setModal(False)
        self.setup_ui()
        self.refresh_ui()

    def setup_ui(self):
        """Setup the UI components"""
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        header_layout = QtWidgets.QHBoxLayout()
        self.title_label = QtWidgets.QLabel(f"Manage {self.app_name} Versions")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        self.layout.addLayout(header_layout)

        self.active_version_group = QtWidgets.QGroupBox("Active Version")
        active_layout = QtWidgets.QHBoxLayout()

        self.active_version_label = QtWidgets.QLabel("None")
        self.active_version_label.setStyleSheet("font-weight: bold; color: green;")
        active_layout.addWidget(QtWidgets.QLabel("Current:"))
        active_layout.addWidget(self.active_version_label)
        active_layout.addStretch()

        self.active_version_group.setLayout(active_layout)
        self.layout.addWidget(self.active_version_group)

        self.versions_group = QtWidgets.QGroupBox("Installed Versions")
        versions_layout = QtWidgets.QVBoxLayout()

        self.versions_list = QtWidgets.QListWidget()
        self.versions_list.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection
        )
        self.versions_list.currentItemChanged.connect(self.on_version_selected)
        versions_layout.addWidget(self.versions_list)

        version_buttons_layout = QtWidgets.QHBoxLayout()

        self.switch_button = QtWidgets.QPushButton("Set as Active")
        self.switch_button.clicked.connect(self.switch_to_selected_version)
        self.switch_button.setEnabled(False)

        self.uninstall_version_button = QtWidgets.QPushButton("Uninstall Version")
        self.uninstall_version_button.clicked.connect(self.uninstall_selected_version)
        self.uninstall_version_button.setEnabled(False)
        self.reshim_button = QtWidgets.QPushButton("Reshim")
        self.reshim_button.clicked.connect(self.reshim_active_version)
        self.reshim_button.setEnabled(True)

        version_buttons_layout.addWidget(self.switch_button)
        version_buttons_layout.addWidget(self.uninstall_version_button)
        version_buttons_layout.addWidget(self.reshim_button)

        versions_layout.addLayout(version_buttons_layout)
        self.versions_group.setLayout(versions_layout)
        self.layout.addWidget(self.versions_group)

        main_buttons_layout = QtWidgets.QHBoxLayout()

        self.install_new_button = QtWidgets.QPushButton("Install New Version")
        self.install_new_button.clicked.connect(self.install_new_version)

        self.uninstall_all_button = QtWidgets.QPushButton("Uninstall All")
        self.uninstall_all_button.clicked.connect(self.uninstall_all_versions)
        self.uninstall_all_button.setStyleSheet("background-color: #ffcccc;")

        main_buttons_layout.addWidget(self.install_new_button)
        main_buttons_layout.addStretch()
        main_buttons_layout.addWidget(self.uninstall_all_button)

        self.layout.addLayout(main_buttons_layout)

        close_layout = QtWidgets.QHBoxLayout()
        close_layout.addStretch()

        self.close_button = QtWidgets.QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        close_layout.addWidget(self.close_button)

        self.layout.addLayout(close_layout)

        self.status_label = QtWidgets.QLabel("")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        self.layout.addWidget(self.status_label)

        self.setFixedSize(500, 450)

    def refresh_ui(self):
        """Refresh the UI with current state"""
        self.app_instance._load_state()
        active_version = self.app_instance.active_version
        installed_versions = self.app_instance.list_installed_versions()
        available_versions = (
            self.app_instance.get_available_versions()
            if hasattr(self.app_instance, "get_available_versions")
            else []
        )
        display_name_map = {}
        for v in available_versions:
            if isinstance(v, dict):
                display_name_map[v.get("real_name", str(v))] = v.get(
                    "display_name", v.get("real_name", str(v))
                )
            else:
                display_name_map[str(v)] = str(v)
        if active_version:
            active_display = display_name_map.get(active_version, active_version)
            self.active_version_label.setText(active_display)
            self.active_version_label.setStyleSheet("font-weight: bold; color: green;")
        else:
            self.active_version_label.setText("None")
            self.active_version_label.setStyleSheet("font-weight: bold; color: red;")
        self.versions_list.clear()
        if installed_versions:
            for version in installed_versions:
                display_name = display_name_map.get(version, version)
                item = QtWidgets.QListWidgetItem(display_name)
                item.setData(QtCore.Qt.ItemDataRole.UserRole, version)
                if version == active_version:
                    item.setText(f"{display_name} (Active)")
                    item.setBackground(QtCore.Qt.GlobalColor.lightGray)
                self.versions_list.addItem(item)
            self.status_label.setText(f"{len(installed_versions)} version(s) installed")
        else:
            self.status_label.setText("No versions installed")
        self.update_button_states()

    def update_button_states(self):
        """Update the enabled state of buttons"""
        has_versions = len(self.app_instance.list_installed_versions()) > 0
        selected_item = self.versions_list.currentItem()
        has_selection = selected_item is not None

        self.uninstall_all_button.setEnabled(has_versions)
        self.switch_button.setEnabled(has_selection)
        self.uninstall_version_button.setEnabled(has_selection)

        if has_selection:
            selected_version = self.get_selected_version()
            is_active = selected_version == self.app_instance.active_version
            self.switch_button.setEnabled(not is_active)

    def on_version_selected(self):
        """Handle version selection in the list"""
        self.update_button_states()

    def get_selected_version(self) -> Optional[str]:
        """Get the currently selected version from the list"""
        current_item = self.versions_list.currentItem()
        if current_item:
            version = current_item.data(QtCore.Qt.ItemDataRole.UserRole)
            return version
        return None

    def install_new_version(self):
        """Install a new version of the application"""
        try:
            available_versions = self.app_instance.get_available_versions()
            installed_versions = self.app_instance.list_installed_versions()

            available_versions = [
                v for v in available_versions if v not in installed_versions
            ]

            if not available_versions:
                QtWidgets.QMessageBox.information(
                    self,
                    "No New Versions",
                    "All available versions are already installed.",
                )
                return

            selected_version = VersionSelectorDialog.select_version(
                self.app_name, available_versions, parent=self
            )

            if selected_version:
                self.app_instance.install(selected_version)
                self.refresh_ui()
                QtWidgets.QMessageBox.information(
                    self,
                    "Installation Complete",
                    f"{self.app_name} {selected_version} installed successfully!",
                )

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Installation Error",
                f"Failed to install {self.app_name}: {str(e)}",
            )

    def switch_to_selected_version(self):
        """Switch to the selected version"""
        selected_version = self.get_selected_version()
        if not selected_version:
            return

        try:
            self.app_instance.switch_version(selected_version)
            self.refresh_ui()
            QtWidgets.QMessageBox.information(
                self,
                "Version Switched",
                f"Successfully switched to {self.app_name} {selected_version}",
            )

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Switch Error",
                f"Failed to switch to {selected_version}: {str(e)}",
            )

    def uninstall_selected_version(self):
        """Uninstall the selected version"""
        selected_version = self.get_selected_version()
        if not selected_version:
            return

        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm Uninstall",
            f"Are you sure you want to uninstall {self.app_name} {selected_version}?",
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            try:
                self.app_instance.uninstall(selected_version)
                self.refresh_ui()
                QtWidgets.QMessageBox.information(
                    self,
                    "Uninstall Complete",
                    f"{self.app_name} {selected_version} uninstalled successfully!",
                )

            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Uninstall Error",
                    f"Failed to uninstall {selected_version}: {str(e)}",
                )

    def uninstall_all_versions(self):
        """Uninstall all versions"""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm Uninstall All",
            f"Are you sure you want to uninstall ALL versions of {self.app_name}?\nThis action cannot be undone.",
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            try:
                self.app_instance.uninstall()
                self.refresh_ui()
                QtWidgets.QMessageBox.information(
                    self,
                    "Uninstall Complete",
                    f"All versions of {self.app_name} uninstalled successfully!",
                )
                self.close()

            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Uninstall Error",
                    f"Failed to uninstall all versions: {str(e)}",
                )

    def reshim_active_version(self):
        """Re-create shims and shortcuts for the currently active version"""
        try:
            active_version = self.app_instance.active_version
            if not active_version:
                QtWidgets.QMessageBox.warning(
                    self,
                    "No Active Version",
                    f"No active version of {self.app_name} to reshim.",
                )
                return

            # Update shims
            self.app_instance._update_shims_for_version(active_version)

            # Update shortcuts if the app has this method
            if hasattr(self.app_instance, "_update_shortcuts_for_version"):
                self.app_instance._update_shortcuts_for_version(active_version)

            QtWidgets.QMessageBox.information(
                self,
                "Reshim Complete",
                f"Shims and shortcuts for {self.app_name} {active_version} have been recreated.",
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Reshim Error", f"Failed to reshim {self.app_name}: {str(e)}"
            )

    def show_manager(self):
        """Show the version manager dialog"""
        self.refresh_ui()
        self.show()
        self.raise_()
        self.activateWindow()
