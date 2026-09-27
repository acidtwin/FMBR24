#!/usr/bin/env python3
# FM24 Homegrown Editor - desktop GUI for patching squad registration in FM24 saves.
# Direction: FM24 default dark skin. See gui/theme.py for the colour palette.
import sys
import faulthandler

_log_path = '/tmp/fm_editor_crash.log'
try:
    _log_file = open(_log_path, 'w', buffering=1)
    faulthandler.enable(file=_log_file)
    sys.stderr = _log_file
except Exception:
    faulthandler.enable()
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from gui.theme import QSS
from gui.main_window import MainWindow
from gui.icon import make_app_icon


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('FM24 Homegrown Editor')
    app.setStyleSheet(QSS)
    icon = make_app_icon()
    app.setWindowIcon(icon)
    window = MainWindow()
    window.setWindowIcon(icon)
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
