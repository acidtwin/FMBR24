#!/usr/bin/env python3
# FM Backroom 24 (FMBR24) - desktop GUI for patching squad registration in FM24 saves.
# Direction: FM24 default dark skin. See gui/theme.py for the colour palette.
import sys
import faulthandler

_log_path = '/tmp/fm_editor_debug.log'
try:
    _log_file = open(_log_path, 'w', buffering=1)
    faulthandler.enable(file=_log_file)
    sys.stderr = _log_file
    sys.stdout = _log_file
except Exception:
    faulthandler.enable()


def _excepthook(t, v, tb):
    # PyQt6 aborts the process on an unhandled exception in a slot unless a hook is installed
    import traceback
    traceback.print_exception(t, v, tb)


sys.excepthook = _excepthook
from PyQt6.QtWidgets import QApplication
from gui.theme import QSS
from gui.main_window import MainWindow
from gui.icon import make_app_icon


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('FM Backroom 24')
    app.setStyleSheet(QSS)
    icon = make_app_icon()
    app.setWindowIcon(icon)
    window = MainWindow()
    window.setWindowIcon(icon)
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
