from PySide6 import QtWidgets, QtCore
from widgets.sidebar import Sidebar
from widgets.categories.Runtimes import Runtimes
from widgets.categories.CodeEditors import CodeEditors
from widgets.nodejs_widget import NodejsWidget
from state_manager import state_manager, PATH_DIR
import os


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Great Windows Environment Manager")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QtWidgets.QHBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.sidebar = Sidebar()
        self.layout.addWidget(self.sidebar)

        self.runtimes_content = Runtimes()
        self.code_editors_content = CodeEditors()
        self.layout.addWidget(self.runtimes_content)
        self.layout.addWidget(self.code_editors_content)

        self.runtimes_content.hide()
        self.code_editors_content.show()

        self.sidebar.code_editors_button.clicked.connect(self.show_code_editors)
        self.sidebar.runtimes_button.clicked.connect(self.show_runtimes)

    def show_code_editors(self):
        self.runtimes_content.hide()
        self.code_editors_content.show()

    def show_runtimes(self):
        self.code_editors_content.hide()
        self.runtimes_content.show()


if __name__ == "__main__":
    PATH_DIR.mkdir(parents=True, exist_ok=True)

    app = QtWidgets.QApplication([])

    if str(PATH_DIR) not in os.environ.get("PATH", ""):
        print(os.environ.get("PATH", ""))
        warning_message = (
            f"Warning: You will not be able to access your installed apps!\n"
            f"Please add: {PATH_DIR} to your PATH environment variable!"
        )
        QtWidgets.QMessageBox.warning(None, "PATH Warning", warning_message)

    style = state_manager.get_style()
    app.setStyle(style)

    window = MainWindow()
    window.show()

    app.exec()
