import signal
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from .main_window import MainWindow


def _install_sigint_handler(app: QApplication) -> None:
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    timer = QTimer(app)
    timer.start(200)
    timer.timeout.connect(lambda: None)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("PyLauncher")
    app.setOrganizationName("PyLauncher")
    _install_sigint_handler(app)
    window = MainWindow()
    window.show()
    return app.exec()