import ctypes
import os
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.config import APP_NAME, resource_path
from app.core import admin
from app.ui.main_window import MainWindow
from app.ui.styles import APP_STYLE


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLE)

    icon_file = resource_path("ico.ico")
    if os.path.isfile(icon_file):
        app.setWindowIcon(QIcon(icon_file))
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "NOXIOUS.NITRO.1")
    except Exception:
        pass

    window = MainWindow()
    if admin.is_admin():
        window.setWindowTitle(window.windowTitle() + "  [ADMIN]")
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
