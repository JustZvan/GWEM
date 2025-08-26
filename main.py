from PySide6 import QtWidgets, QtCore
from PySide6.QtGui import QIcon, QAction
from widgets.sidebar import Sidebar
from widgets.categories.Runtimes import Runtimes
from widgets.categories.CodeEditors import CodeEditors
from widgets.categories.Plugins import Plugins
from widgets.categories.GameEngines import GameEngines
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
        self.plugins_content = Plugins()
        self.game_engines_content = GameEngines()
        self.layout.addWidget(self.runtimes_content)
        self.layout.addWidget(self.code_editors_content)
        self.layout.addWidget(self.plugins_content)
        self.layout.addWidget(self.game_engines_content)

        self.runtimes_content.hide()
        self.code_editors_content.show()
        self.plugins_content.hide()
        self.game_engines_content.hide()

        self.sidebar.code_editors_button.clicked.connect(self.show_code_editors)
        self.sidebar.runtimes_button.clicked.connect(self.show_runtimes)
        self.sidebar.plugins_button.clicked.connect(self.show_plugins)
        self.sidebar.game_engines_button.clicked.connect(self.show_game_engines)

        self.create_menubar()

    def create_menubar(self):
        menubar = self.menuBar()
        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def show_about_dialog(self):
        about_dialog = QtWidgets.QMessageBox(self)
        about_dialog.setWindowTitle("About GWEM")
        about_dialog.setIconPixmap(QIcon("assets/icon.ico").pixmap(64, 64))
        about_dialog.setText("<b>GWEM</b><br>Licensed GPLv3<br>Created by JustZvan")
        about_dialog.exec()

    def show_code_editors(self):
        self.runtimes_content.hide()
        self.code_editors_content.show()
        self.plugins_content.hide()
        self.game_engines_content.hide()

    def show_runtimes(self):
        self.code_editors_content.hide()
        self.runtimes_content.show()
        self.plugins_content.hide()
        self.game_engines_content.hide()

    def show_plugins(self):
        self.runtimes_content.hide()
        self.code_editors_content.hide()
        self.plugins_content.show()
        self.game_engines_content.hide()

    def show_game_engines(self):
        self.runtimes_content.hide()
        self.code_editors_content.hide()
        self.plugins_content.hide()
        self.game_engines_content.show()


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

    icon = QIcon()
    icon.addFile("assets/icon.ico")

    window = MainWindow()
    window.setWindowIcon(icon)
    window.show()

    app.exec()
