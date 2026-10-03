#!/usr/bin/env python3
"""Regenerate every README screenshot in docs/screenshots/ from a real FM24 save (read-only).

Usage:
    python3 scripts/make_screenshots.py /path/to/save.fm
    FMBR24_SAVE=/path/to/save.fm python3 scripts/make_screenshots.py [--out DIR] [--only NAME ...]

Runs fully offscreen (QT_QPA_PLATFORM=offscreen) with a throw-away FMBR24_CONFIG_DIR, so the user's real
settings are never touched. The save is only ever read: the one queued Homegrown change shown on the Squads
shot lives in memory and is discarded at the end (nothing is saved). Parsing the save takes about a minute.

Needs PyQt6, zstandard, numpy (requirements.txt). Pillow is optional: with it each PNG is quantised to 256
colours (each shot stays well under ~400 KB); without it the raw grabs are written.

Which player / club / page is shown is deterministic: the manager's own club, its highest-CA player, and so on.
Add a shot = write a function and add it to SHOTS (name -> function(ctx)); the name is the file stem.
"""
import argparse
import os
import sys
import tempfile
import time

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['FMBR24_CONFIG_DIR'] = tempfile.mkdtemp(prefix='fmbr24_shots_')  # never the real settings.json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from PyQt6.QtCore import Qt  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

from gui.theme import QSS  # noqa: E402
import gui.main_window as M  # noqa: E402
from gui.player_window import PlayerWindow  # noqa: E402

WIN_W, WIN_H = 1440, 900
app = QApplication.instance() or QApplication([])
app.setStyleSheet(QSS)


def pump(n=3):
    """Let Qt lay out wrapped labels / replaced widgets before a grab (needs more than one pass)."""
    for _ in range(n):
        app.processEvents()
        time.sleep(0.02)
    app.processEvents()


def load(w, path):
    from fm_editor import settings as S  # fresh parse every run: the parse cache holds ~170 fewer staff than a fresh parse
    S.save({**S.load(), 'use_cache': False, 'faces_enabled': False,
            'logos_enabled': False, 'flags_enabled': False})  # no third-party facepack pictures, club logos or flags in published shots
    w._load_path(path)
    t0 = time.time()
    while w._save_data is None or w._busy:
        app.processEvents()
        time.sleep(0.01)
        if time.time() - t0 > 900:
            raise SystemExit('Timed out parsing the save')


def pick_player(w):
    """The manager's own club (opened on Squads) and its squad, best CA first: squad[0] is the player-window subject."""
    sd = w._save_data
    club = next(c for c in sd['clubs'] if c['id'] == sd['save_info']['manager_club_id'])
    w._show_squad(club)
    pump()
    squad = sorted(w._squad, key=lambda p: (-p.get('ca', 0), p['name']))
    return club, squad


# -- shots: each takes ctx = {'w': MainWindow, 'club': dict, 'squad': [person]} and returns a QWidget to grab ----

def save_info(c):
    c['w']._nav_to('save_info')
    return c['w']


def club(c):
    c['w']._show_squad(c['club'])
    c['w']._nav_to('club')
    return c['w']


def squads(c):
    """Squads with a queued Homegrown change: yellow row + HGP/HGC badges. Memory only, never saved."""
    w = c['w']
    w._show_squad(c['club'])
    w._nav_to_squad_view()
    pump()
    t = w._table
    t.sortByColumn(3, Qt.SortOrder.DescendingOrder)  # CA, best first
    pump()
    for r in range(t.rowCount()):
        pid = t.item(r, 0).data(Qt.ItemDataRole.UserRole)
        p = next(p for p in w._squad if p.get('id') == pid)
        if not p.get('hgp') and w._can_patch(p):
            t.selectRow(r)
            w._queue_selected('hgp')  # queue only; Save Changes is never called
            t.clearSelection()
            break
    pump()
    return w


def players(c):
    w = c['w']
    w._open_players_view()
    w._players_table.sortByColumn(3, Qt.SortOrder.DescendingOrder)  # CA, best first
    return w


def report(c):
    w = c['w']
    w._run_report('prospects')
    w._reports_table.sortByColumn(4, Qt.SortOrder.DescendingOrder)  # PA, best first
    return w


def settings(c):
    c['w']._nav_to('settings')
    return c['w']


def compare(c):
    """Compare Players: the two best outfield players of the manager's club, Detailed radar."""
    from fm_editor.player_search import is_keeper
    w = c['w']
    a, b = [p for p in c['squad'] if not is_keeper(p)][:2]
    w._open_compare(a, b)
    w._compare_page.set_mode('detailed')
    pump()
    return w


def _player(c, tab):
    w = c['w']
    p = c['squad'][0]
    sd = w._save_data
    dlg = PlayerWindow(p, sd, sd['squads'][p['id']] + 1, w, can_patch=w._can_patch(p), queue=w)
    dlg.resize(1122, 860)
    dlg.show()
    dlg._select_tab(tab)
    pump()
    return dlg


def pw(tab):
    def f(c):
        return _player(c, tab)
    return f


SHOTS = {
    'save-info': save_info,
    'club': club,
    'squads': squads,
    'player-profile': pw('profile'),
    'player-contract': pw('contract'),
    'player-positions': pw('positions'),
    'player-role-rating': pw('role'),
    'compare': compare,
    'scouting-players': players,
    'player-report': report,
    'settings': settings,
}


def write_png(widget, path):
    widget.grab().save(path)
    try:
        from PIL import Image
        im = Image.open(path).convert('RGB')
        im.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(path, optimize=True)
    except ImportError:
        pass


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('save', nargs='?', default=os.environ.get('FMBR24_SAVE'), help='FM24 .fm save (or set FMBR24_SAVE)')
    ap.add_argument('--manager-name', default='Manager',
                    help="name shown for the manager (default hides the real one; pass '' to keep it)")
    ap.add_argument('--out', default=os.path.join(ROOT, 'docs', 'screenshots'))
    ap.add_argument('--only', nargs='*', choices=sorted(SHOTS), help='regenerate just these shots')
    a = ap.parse_args()
    if not a.save or not os.path.isfile(a.save):
        ap.error('give the path to an FM24 .fm save (argument or FMBR24_SAVE)')
    os.makedirs(a.out, exist_ok=True)

    w = M.MainWindow()
    w.resize(WIN_W, WIN_H)
    w.show()
    load(w, a.save)
    pump()
    if a.manager_name:
        w._save_data['save_info']['manager_name'] = a.manager_name
    club_, squad = pick_player(w)
    ctx = {'w': w, 'club': club_, 'squad': squad}
    for name, fn in SHOTS.items():
        if a.only and name not in a.only:
            continue
        target = fn(ctx)
        pump()
        out = os.path.join(a.out, name + '.png')
        write_png(target, out)
        print(f'{name}: {os.path.getsize(out) // 1024} KB')
        if target is not w:
            target.close()
        w._queue.clear()
        w._queue_changed()  # the queued HGP (Squads shot) must not leak into later shots
    sys.stdout.flush()
    os._exit(0)  # skip Qt teardown of the parsed save


if __name__ == '__main__':
    main()
