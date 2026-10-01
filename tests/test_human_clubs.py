"""human_club_ids / human_pids (fm_editor/saveinfo.py) on synthetic data, then the real save and the
PlayerWindow HGP/HGC visibility (skipped if the save is absent). Plain script: python3 tests/test_human_clubs.py
"""
import os
import struct
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fm_editor.saveinfo import human_club_ids, human_pids  # noqa: E402

SAVE = os.path.expanduser(
    '~/.local/share/Steam/steamapps/compatdata/2252570/pfx/drive_c/users/steamuser/'
    'Documents/Sports Interactive/Football Manager 2024/games/'
    '2026-27 START - Acid Twin Spurs.fm')


def _humans(pids):
    d = b'\x03\x01tad.' + struct.pack('<HH', 0x13, len(pids))
    for pid in pids:
        d += struct.pack('<I', pid) + struct.pack('<HHII', 0x1b, 0x21, 0xbb, 0x6a) + b'\x00\x00\x80\xbf' + b'kit\x00'
    return d


def _job(club_entity):  # 16-byte linked record: club entity id, b10=1, b11=3
    return struct.pack('<I', club_entity) + bytes(6) + b'\x01\x03' + bytes(4)


def test_synthetic():
    assert human_pids(_humans([77])) == [77]
    assert human_pids(_humans([77, 88])) == [77, 88]
    assert human_pids(b'') == [] and human_pids(b'garbage-garbage') == []
    # two humans, two clubs (ids 10 and 20 -> entity 11 / 21); people 'end' offsets into b
    b = bytearray(200)
    for off, ent in ((0, 11), (100, 21)):
        b[off + 34] = 1
        b[off + 35:off + 51] = _job(ent)
    people = [{'id': 77, 'end': 0}, {'id': 88, 'end': 100}, {'id': 5, 'end': 150}]
    sd = {'b': b, 'people': people, 'clubs': [{'id': 10}, {'id': 20}, {'id': 30}], 'save_info': {'manager_club_id': 10}}
    assert human_club_ids(sd, _humans([77, 88])) == {10, 20}
    assert human_club_ids(sd, _humans([77])) == {10}
    assert human_club_ids(sd) == {10}  # no humans.dat: falls back to save_info
    assert human_club_ids({'save_info': {}}) == set()


def test_real_save():
    from gui.workers import ParseWorker
    import fm_editor.cache as cache
    cache._CACHE_DIR = tempfile.mkdtemp()  # never touch ~/.cache
    out = {}
    w = ParseWorker(SAVE, use_cache=False)
    w.done.connect(lambda r: out.update(r))
    w.run()
    sd = out
    assert sd['human_clubs'] == {492}, sd['human_clubs']  # Tottenham
    spurs = next(p for p in sd['people'] if sd['squads'].get(p.get('id')) == 492)
    other = next(p for p in sd['people'] if sd['squads'].get(p.get('id')) not in (None, 492))

    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PyQt6.QtWidgets import QApplication, QPushButton
    app = QApplication.instance() or QApplication([])
    from gui.player_window import PlayerWindow
    for person, want in ((spurs, True), (other, False)):
        club = sd['squads'][person['id']]
        w = PlayerWindow(person, sd, club + 1, None, can_patch=club in sd['human_clubs'])
        texts = {b.text() for b in w.findChildren(QPushButton)}
        has = any(t.startswith('Make ') or t.endswith(' set') for t in texts)
        assert has == want and 'Close' in texts and 'Add to Shortlist' in texts, texts
        app.processEvents()
        w.grab().save(os.path.join(tempfile.gettempdir(), f'pw_{"human" if want else "other"}.png'))


if __name__ == '__main__':
    test_synthetic()
    print('OK: synthetic')
    if os.path.exists(SAVE):
        test_real_save()
        print('OK: real save + PlayerWindow')
    else:
        print('SKIP: save file not found')
