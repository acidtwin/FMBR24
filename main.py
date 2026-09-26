#!/usr/bin/env python3
# FM24 Homegrown Editor — desktop GUI for patching squad registration in FM24 saves.
# Direction: FM24 default dark skin. See gui/theme.py for the colour palette.
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from gui.theme import QSS
from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('FM24 Homegrown Editor')
    app.setStyleSheet(QSS)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
