"""Season player stats (rgman/player_stats.dat) + Club page 'Top Players' ranking.

Ground truth = the user's in-game Squad screen and Micky van de Ven's player profile
(Tottenham, game date 2 Jan 2028). Run directly: python3 tests/test_player_stats.py
(the real-save part skips politely if the save is absent).
"""
import os
os.environ['FMBR24_CONFIG_DIR'] = __import__('tempfile').mkdtemp()  # never the user's real settings
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SAVE = os.path.expanduser(
    '~/.local/share/Steam/steamapps/compatdata/2252570/pfx/drive_c/users/steamuser/'
    'Documents/Sports Interactive/Football Manager 2024/games/'
    '2026-27 START - Acid Twin Spurs.fm')
from tests.snapshot import save_path, snapshot_mode  # noqa: E402
SAVE = save_path(SAVE)

# person id: (starts, subs, goals, assists, minutes or None if only ~known, POM, avg rating)
GT = {
    72793: (27, 0, 0, 0, None, 0, 6.88),     # Diogo Costa
    84523: (22, 5, 5, 13, None, 4, 7.52),    # Michael Kayode
    39683: (27, 1, 2, 2, None, 0, 6.94),     # Jan Paul van Hecke
    39811: (24, 4, 2, 2, None, 0, 7.01),     # Micky van de Ven
    62830: (20, 1, 1, 12, None, 2, 7.33),    # Alejandro Balde
    44427: (22, 4, 4, 5, None, 1, 7.05),     # Sandro Tonali
    48650: (12, 15, 3, 3, 1281, 2, 7.11),    # Manu Koné
    101766: (24, 1, 18, 5, None, 4, 7.58),   # Nicolás Paz
    62466: (19, 3, 9, 5, None, 4, 7.35),     # Xavi Simons
    114911: (18, 4, 12, 2, None, 0, 7.29),   # Rodrigo Mora
    109583: (23, 2, 13, 1, 1961, 0, 6.99),   # Endrick
    106179: (3, 0, 0, 0, 270, 0, 6.63),      # Christian Zawieschitzky
    57054: (7, 12, 0, 0, 791, 0, 6.86),      # Strahinja Pavlović
    102754: (20, 4, 6, 3, 1718, 1, 7.05),    # Aleksandar Pavlović
    14104: (5, 15, 2, 4, 676, 1, 6.96),      # Lionel Messi
    45951: (2, 5, 0, 0, 265, 0, 6.67),       # Giorgio Scalvini
    61914: (13, 6, 1, 9, None, 2, 7.34),     # Pedro Porro
    25257: (2, 6, 1, 0, 251, 0, 6.52),       # Neymar
    102613: (6, 4, 2, 0, 462, 1, 7.09),      # Lucas Bergvall
    79120: (1, 7, 3, 1, 177, 1, 7.53),       # Omar Marmoush
    83137: (17, 5, 4, 6, None, 1, 7.11),     # Sávio
    94152: (8, 4, 2, 2, 736, 1, 6.84),       # Gianluca Prestianni
    104753: (3, 5, 0, 2, 327, 0, 7.16),      # Álvaro Montoro
    133061: (0, 2, 0, 0, 38, 0, 6.70),       # Luca Williams-Barnett
}


def test_overall_block_and_rating():
    from fm_editor.playerstats import overall_block, rating
    # (rating sum x10, minutes, starts, subs, rated, goals, assists, pom)
    league = (1324, 1482, 17, 2, 19, 1, 1, 0)
    cups = (221, 201, 2, 1, 3, 1, 0, 0)
    cont = (417, 464, 5, 1, 6, 0, 1, 0)
    overall = tuple(a + b + c for a, b, c in zip(league, cups, cont))
    friendlies = (389, 450, 5, 0, 5, 3, 2, 0)
    last_match = (70, 71, 1, 0, 1, 0, 0, 0)
    empty = (0,) * 8
    assert overall_block([friendlies, league, cups, cont, overall, last_match, empty]) == overall
    # a player without an overall block (no subset sums to any block) yields None, not a guess
    assert overall_block([friendlies, league, empty]) is None
    assert overall_block([empty]) is None
    assert rating(1962, 28) == 7.01 and rating(1324, 19) == 6.97 and rating(0, 0) is None


def test_club_top_players():
    from gui.main_window import _club_top_players

    def pl(name, ca, rating=None, rated=0, pos='GK'):
        p = {'name': name, 'ca': ca, 'positions': [1] * 15}
        if rating is not None:
            p['stats'] = {'rating': rating, 'rated': rated}
        return p
    squad = [pl('A', 100, 7.2, 20), pl('B', 120, 7.2, 20),   # tie on rating and apps -> higher CA first
             pl('C', 90, 7.9, 4),                            # below 40% of 20 = 8 rated apps -> excluded
             pl('D', 150, 6.5, 25),                          # most used player (GK included) sets the floor
             pl('E', 80, 7.0, 12), pl('F', 80, 6.9, 12), pl('G', 70), pl('H', 70, 7.0, 10),
             pl('I', 60, 7.3, 11)]
    mode, top = _club_top_players(squad)
    assert mode == 'rating'
    names = [p['name'] for p, _, _ in top]
    assert names == ['I', 'B', 'A', 'E', 'H', 'F', 'D'], names   # 40% of 25 = 10 rated apps; C, G out
    assert [t for _, t, _ in top][:3] == ['7.30', '7.20', '7.20']
    assert [g for _, _, g in top] == [True, True, True, True, True, False, False]  # >= 7.00 is "good"
    assert _club_top_players(squad, n=3)[1][0][0]['name'] == 'I'
    # fewer than 3 eligible players -> honest CA fallback, values are the CA
    mode, top = _club_top_players([pl('X', 50, 7.0, 10), pl('Y', 70), pl('Z', 70)])
    assert mode == 'ca' and [(p['name'], t) for p, t, _ in top] == [('Y', '70'), ('Z', '70'), ('X', '50')]
    assert _club_top_players([]) == ('ca', [])


def test_spurs_stats_vs_game():
    from fm_editor.archive import parse_archive, get_member
    from fm_editor.playerstats import find_records, _blocks, parse_player_stats

    _, members, _, _, _, _ = parse_archive(SAVE)
    data = get_member(SAVE, next(m for m in members if m['name'] == 'rgman/player_stats.dat'))
    everyone = parse_player_stats(data, range(1, 200_000))  # all person ids, like ParseWorker
    stats = {pid: everyone[pid] for pid in GT}
    exact = snapshot_mode(SAVE)
    for pid, (st, sub, g, a, mins, pom, rat) in GT.items():
        s = stats[pid]
        if exact:  # in-game Squad screen values at the snapshot date
            assert (s['starts'], s['subs'], s['goals'], s['assists'], s['pom']) == (st, sub, g, a, pom), (pid, s)
            assert s['apps'] == st + sub
            assert mins is None or s['mins'] == mins, (pid, s)
            assert abs(s['rating'] - rat) < 0.005, (pid, s)
        else:  # the save has moved on: invariants only
            assert s['apps'] == s['starts'] + s['subs'] and s['rated'] <= s['apps'] and s['mins'] >= 0, (pid, s)
            assert 1 <= s['rating'] <= 10, (pid, s)
    # per-competition blocks of van de Ven (profile screen): league 17(2) 6.97, CL 5(1) 6.95,
    # friendlies 5(0) 7.78, Carabao + Community Shield 2(1) (goal from the Shield), overall 24(4) 7.01
    blocks = _blocks(find_records(data, range(1, 200_000))[39811])
    if exact:
        assert (1324, 1482, 17, 2, 19, 1, 1, 0) == blocks[1][:7] + (blocks[1][7],)
        assert (417, 464, 5, 1, 6, 0, 1) == blocks[3][:7]
        assert (389, 450, 5, 0, 5, 3, 2) == blocks[0][:7]
        assert (221, 201, 2, 1, 3, 1, 0) == blocks[2][:7]
        assert (1962, 2147, 24, 4, 28, 2, 2) == blocks[5][:7]
    # population sanity: ratings 4-10, nobody has more than 70 apps or 4,800 minutes
    assert len(everyone) > 20_000
    lo = 4.0 if exact else 1.0  # the live save has real 3.85 ratings (2 apps); 4-10 holds at the snapshot date
    assert all(lo <= s['rating'] <= 10.0 for s in everyone.values() if s['rating'])
    assert all(s['apps'] == s['starts'] + s['subs'] and s['rated'] <= s['apps'] and s['mins'] >= 0 for s in everyone.values())
    assert max(s['apps'] for s in everyone.values()) <= 70 and max(s['mins'] for s in everyone.values()) < 4800


if __name__ == '__main__':
    test_overall_block_and_rating()
    test_club_top_players()
    if not os.path.exists(SAVE):
        print('SKIPPED (save not found): test_player_stats real-save part')
    else:
        test_spurs_stats_vs_game()
    print('OK')
