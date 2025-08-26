from PySide6 import QtWidgets, QtCore
from PySide6.QtGui import QIcon, QAction
from widgets.sidebar import Sidebar
from widgets.categories.Runtimes import Runtimes
from widgets.categories.CodeEditors import CodeEditors
from widgets.categories.Plugins import Plugins
from widgets.categories.GameEngines import GameEngines
from state_manager import state_manager, PATH_DIR
import os

styles = """
QMainWindow {
    background-color: #000000;
    color: #ffffff;
}

QWidget {
    background-color: #000000;
    color: #ffffff;
    border: none;
    margin: 0px;
    padding: 0px;
}

QPushButton {
    background-color: #1a1a1a;
    color: #ffffff;
    border: 1px solid #333333;
    padding: 4px 8px;
    margin: 1px;
    border-radius: 2px;
}

QPushButton:hover {
    background-color: #2a2a2a;
    border: 1px solid #555555;
}

QPushButton:pressed {
    background-color: #0a0a0a;
    border: 1px solid #666666;
}

QMenuBar {
    background-color: #000000;
    color: #ffffff;
    border: none;
    padding: 2px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 4px 8px;
    margin: 1px;
}

QMenuBar::item:selected {
    background-color: #1a1a1a;
    border: 1px solid #333333;
}

QMenu {
    background-color: #000000;
    color: #ffffff;
    border: 1px solid #333333;
    padding: 2px;
}

QMenu::item {
    padding: 4px 16px;
    margin: 1px;
}

QMenu::item:selected {
    background-color: #1a1a1a;
}

QScrollArea {
    background-color: #000000;
    border: none;
    margin: 2px;
    padding: 2px;
}

QScrollBar:vertical {
    background-color: #1a1a1a;
    width: 12px;
    border: none;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #333333;
    min-height: 20px;
    border-radius: 2px;
    margin: 1px;
}

QScrollBar::handle:vertical:hover {
    background-color: #555555;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}

QScrollBar:horizontal {
    background-color: #1a1a1a;
    height: 12px;
    border: none;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background-color: #333333;
    min-width: 20px;
    border-radius: 2px;
    margin: 1px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #555555;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    border: none;
    background: none;
}

QLabel {
    background-color: transparent;
    color: #ffffff;
    padding: 2px;
    margin: 1px;
}

QFrame {
    background-color: #000000;
    border: none;
    margin: 2px;
    padding: 2px;
}

QMessageBox {
    background-color: #000000;
    color: #ffffff;
}

QMessageBox QPushButton {
    min-width: 60px;
    padding: 4px 12px;
}

QDialog {
    background-color: #000000;
    color: #ffffff;
}

QGroupBox {
    background-color: #000000;
    color: #ffffff;
    border: 1px solid #333333;
    border-radius: 3px;
    margin: 4px 0px;
    padding-top: 8px;
    font-weight: bold;
}

QGroupBox::title {
    color: #ffffff;
    subcontrol-origin: margin;
    left: 8px;
    padding: 0px 4px;
}

QListWidget {
    background-color: #1a1a1a;
    color: #ffffff;
    border: 1px solid #333333;
    border-radius: 2px;
    padding: 2px;
    selection-background-color: #2a2a2a;
}

QListWidget::item {
    padding: 4px;
    margin: 1px;
    border-radius: 2px;
}

QListWidget::item:selected {
    background-color: #2a2a2a;
    border: 1px solid #555555;
}

QListWidget::item:hover {
    background-color: #1f1f1f;
}

/* Force override inline styles for version manager */
QLabel[class="version-label"] {
    color: #00ff00 !important;
}

/* Status and info labels */
QLabel {
    color: #ffffff;
}

/* Override any hardcoded green/red colors */
*[style*="color: green"] {
    color: #00ff00 !important;
}

*[style*="color: red"] {
    color: #ff4444 !important;
}

*[style*="color: #666"] {
    color: #cccccc !important;
}

*[style*="color: #333"] {
    color: #cccccc !important;
}
"""


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

    app.setStyle("Fusion")
    app.setStyleSheet(styles)

    icon = QIcon()
    icon.addFile("assets/icon.ico")

    window = MainWindow()
    window.setWindowIcon(icon)
    window.show()

    app.exec()
