"""App icon: loaded from the pre-rendered size ladder in resources/icons/."""
import os
from PyQt6.QtGui import QIcon

_ICON_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         'resources', 'icons')
_SIZES = (16, 24, 32, 48, 64, 128, 256, 512)


def make_app_icon():
    icon = QIcon()
    for n in _SIZES:
        icon.addFile(os.path.join(_ICON_DIR, f'icon-{n}.png'))
    return icon
