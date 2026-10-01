"""About dialog: name, version, purpose, legal line, credits, repo (plain text, no network)."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from fm_editor import settings as _settings
from gui.icon import make_app_icon
from gui.theme import COLORS

PURPOSE = 'Browse your Football Manager 24 saves: squads, staff, scouting and reports, with homegrown (HGP/HGC) patching.'
CREDITS = ('Trait recommender data: GuideToFM and the author of the trait sheet. '
           'Save-format reverse engineering is original work.')


def _qss():
    c = COLORS
    return f"""
QDialog#aboutDialog {{ background:{c['window_bg']}; }}
QDialog#aboutDialog QWidget {{ background:transparent; }}
QDialog#aboutDialog QLabel {{ color:{c['text_secondary']}; font-size:12px; }}
QDialog#aboutDialog QLabel#aboutName {{ color:{c['text_primary']}; font-size:20px; font-weight:700; }}
QDialog#aboutDialog QLabel#aboutVer {{ color:{c['text_dim']}; font-size:11px; }}
QDialog#aboutDialog QLabel#aboutRepo {{ color:{c['accent_hover']}; }}
QDialog#aboutDialog QPushButton {{ background:{c['accent']}; color:#fff; border:none;
    border-radius:3px; padding:5px 18px; font-size:12px; }}
QDialog#aboutDialog QPushButton:hover {{ background:{c['accent_hover']}; }}
"""


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('aboutDialog')
        self.setWindowTitle('About FMBR24')
        self.setFixedWidth(460)
        self.setStyleSheet(_qss())

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 18)
        lay.setSpacing(12)

        head = QHBoxLayout()
        head.setSpacing(14)
        logo = QLabel()
        logo.setFixedSize(56, 56)
        logo.setPixmap(make_app_icon().pixmap(56, 56))
        names = QVBoxLayout()
        names.setSpacing(2)
        name = QLabel(_settings.APP_NAME)
        name.setObjectName('aboutName')
        ver = QLabel(f'Version {_settings.APP_VERSION}')
        ver.setObjectName('aboutVer')
        names.addStretch()
        names.addWidget(name)
        names.addWidget(ver)
        names.addStretch()
        head.addWidget(logo)
        head.addLayout(names, 1)
        lay.addLayout(head)

        for text, oid in ((PURPOSE, None), (CREDITS, None),
                          (_settings.LEGAL_LINE, None), (_settings.APP_REPO_URL, 'aboutRepo')):
            lbl = QLabel(text)
            lbl.setWordWrap(True)
            if oid:
                lbl.setObjectName(oid)
                lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            lay.addWidget(lbl)

        close = QPushButton('Close')
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.setDefault(True)
        close.clicked.connect(self.accept)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(close)
        lay.addLayout(row)
