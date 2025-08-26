from PySide6 import QtWidgets, QtCore
from typing import List, Optional


class VersionSelectorDialog(QtWidgets.QDialog):
    def __init__(self, app_name: str, available_versions: List, parent=None):
        super().__init__(parent)
        self.app_name = app_name
        self.available_versions = available_versions
        self.selected_version = None
        self._setup_ui()

    def _setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle(f"Select {self.app_name} Version")
        self.setModal(True)
        self.setFixedSize(400, 300)

        layout = QtWidgets.QVBoxLayout()

        header_label = QtWidgets.QLabel(
            f"Select a version of {self.app_name} to install:"
        )
        header_label.setStyleSheet(
            "font-weight: bold; font-size: 14px; margin-bottom: 10px; color: #ffffff;"
        )
        layout.addWidget(header_label)

        self.version_list = QtWidgets.QListWidget()
        self.version_list.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection
        )

        for version_obj in self.available_versions:
            if isinstance(version_obj, dict):
                display_name = version_obj.get(
                    "display_name", version_obj.get("real_name", str(version_obj))
                )
            else:
                display_name = str(version_obj)
            item = QtWidgets.QListWidgetItem(display_name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, version_obj)
            self.version_list.addItem(item)

        if self.available_versions:
            self.version_list.setCurrentRow(0)

        layout.addWidget(self.version_list)

        info_group = QtWidgets.QGroupBox("Version Information")
        info_layout = QtWidgets.QVBoxLayout()

        self.info_label = QtWidgets.QLabel("Select a version to see details")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #cccccc; font-style: italic;")
        info_layout.addWidget(self.info_label)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        button_layout = QtWidgets.QHBoxLayout()

        self.install_button = QtWidgets.QPushButton("Install")
        self.install_button.setDefault(True)
        self.install_button.clicked.connect(self.accept)

        self.cancel_button = QtWidgets.QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.install_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        self.version_list.currentItemChanged.connect(self._on_version_changed)
        self.version_list.itemDoubleClicked.connect(self.accept)

        self._on_version_changed()

    def _on_version_changed(self):
        """Handle version selection change"""
        current_item = self.version_list.currentItem()
        if current_item:
            version_obj = current_item.data(QtCore.Qt.ItemDataRole.UserRole)
            if isinstance(version_obj, dict):
                display_name = version_obj.get(
                    "display_name", version_obj.get("real_name", str(version_obj))
                )
                real_name = version_obj.get("real_name", display_name)
            else:
                display_name = str(version_obj)
                real_name = display_name
            self.selected_version = real_name
            self.info_label.setText(f"Version {display_name} will be installed")
            self.info_label.setStyleSheet("color: #ffffff;")
            self.install_button.setEnabled(True)
        else:
            self.selected_version = None
            self.info_label.setText("Select a version to see details")
            self.info_label.setStyleSheet("color: #cccccc; font-style: italic;")
            self.install_button.setEnabled(False)

    def get_selected_version(self) -> Optional[str]:
        """Get the selected version"""
        return self.selected_version

    @staticmethod
    def select_version(
        app_name: str, available_versions: List[str], parent=None
    ) -> Optional[str]:
        """Static method to show dialog and return selected version"""
        if not available_versions:
            QtWidgets.QMessageBox.warning(
                parent,
                "No Versions Available",
                f"No versions are available for {app_name}",
            )
            return None

        dialog = VersionSelectorDialog(app_name, available_versions, parent)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            return dialog.get_selected_version()
        return None
