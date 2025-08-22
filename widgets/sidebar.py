from PySide6 import QtWidgets, QtCore


class Sidebar(QtWidgets.QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)

        self.sidebar_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.sidebar_layout)

        self.code_editors_button = QtWidgets.QPushButton("Code Editors")
        self.sidebar_layout.addWidget(self.code_editors_button)

        self.runtimes_button = QtWidgets.QPushButton("Languages")
        self.sidebar_layout.addWidget(self.runtimes_button)

        self.plugins_button = QtWidgets.QPushButton("Plugins")
        self.sidebar_layout.addWidget(self.plugins_button)

        self.setFixedWidth(200)

        self.sidebar_layout.addStretch(1)
