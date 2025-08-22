from PySide6 import QtWidgets, QtCore


class NodejsWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout()
        title = QtWidgets.QLabel("Node.js")
        description = QtWidgets.QLabel("The bulky JavaScript runtime.")
        install_button = QtWidgets.QPushButton("Install Node.js")
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(install_button)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Minimum
        )
        self.setMaximumWidth(200)
        self.setMaximumHeight(self.sizeHint().height())
        self.install_button = install_button
