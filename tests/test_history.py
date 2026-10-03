"""Career history (fm_editor/history.py). Ground truth = real careers (Kane, Rice, Grealish, van de Ven, Mbappe,
Pochettino, Guardiola, Mourinho, Arteta). Run directly: python3 tests/test_history.py (about 60 s; the synthetic
current-row tests always run, the real-save part skips politely when the snapshot or the FM install database is
absent)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.snapshot import snapshot_save, skip_if_missing, assert_snapshot  # noqa: E402  (frozen 2028-01-02 copy, never the live save)
SAVE = snapshot_save()

# person id: (identity uid, name)
PLAYERS = {32446: (28049320, 'Harry Kane'), 33096: (28106491, 'Declan Rice'), 32666: (28067800, 'Jack Grealish'),
           39811: (37084591, 'Micky van de Ven'), 74902: (85139014, 'Kylian Mbappé')}
STAFF = {127: (1120, 'Pep Guardiola'), 362: (4059, 'Mauricio Pochettino'), 10510: (4211801, 'José Mourinho'),
         13654: (6701089, 'Mikel Arteta')}


def _sd(clubs=(), squads=None, sub=None, emp=None):
    return {'clubs': list(clubs), 'squads': squads or {}, 'sub_squads': sub or {}, 'employment': emp or {}}


def _club(i, name, nation=1):
    return {'id': i, 'uid': 1000 + i, 'name': name, 'nation': nation}


def _stored(*rows):
    """A career_for_person result of the stored history: rows = (year, club uid)."""
    return {'status': 'ok' if rows else 'none', 'rows': [
        {'year': y, 'club_uid': u, 'club': 'c%d' % u, 'kind': None, 'apps': 5, 'goals': 1, 'season': '%d/%02d' % (y, (y + 1) % 100),
         'current': False, 'from_save': False} for y, u in rows]}


def test_current_row():
    """Rule: a player with a club always gets his CURRENT season row (squad > youth/reserve array > contract
    club), loan = parent row then loan row, no duplicate of a season the rows already hold, free agent untouched."""
    import datetime
    from fm_editor import history as H
    from fm_editor.agecalc import set_ref
    set_ref('2028-01-02')                                     # season 2027/28
    A, B, P, O = _club(1, 'A FC'), _club(2, 'B FC'), _club(3, 'Parent FC'), _club(4, 'Oslo FC', nation=160)
    sd = _sd([A, B, P, O], squads={10: 1, 12: 2, 13: 1, 16: 4}, sub={1: {19: [14]}}, emp={15: 3})

    def cur(person, out):
        H._add_current(out, person, sd)
        return out['rows']
    # young one-club player: no stored history -> exactly one row (his club), apps/goals from stats
    r = cur({'id': 10, 'stats': {'apps': 7, 'goals': 2}}, _stored())
    assert len(r) == 1 and (r[0]['season'], r[0]['club'], r[0]['kind'], r[0]['apps'], r[0]['goals']) == ('2027/28', 'A FC', None, 7, 2), r
    assert r[0]['current'] and r[0]['club_uid'] == A['uid']
    # no stats -> blank
    r = cur({'id': 10}, _stored())
    assert (r[0]['apps'], r[0]['goals']) == (None, None)
    # current club missing from the stored rows: appended last, stored rows untouched
    st = _stored((2022, 2000 + 1), (2023, 2000 + 2))
    before = [dict(x) for x in st['rows']]
    r = cur({'id': 10}, st)
    assert r[:2] == before and len(r) == 3 and r[2]['club'] == 'A FC' and r[2]['season'] == '2027/28'
    # the stored rows already hold this season at that club (uid 1001) -> not duplicated
    r = cur({'id': 10}, _stored((2026, 1001), (2027, 1001)))
    assert len(r) == 2 and not any(x.get('current') for x in r), r
    # older stay at the same club does not count as the current season
    assert len(cur({'id': 10}, _stored((2023, 1001)))) == 2
    # loan: parent first (blank apps), then the loan club with the stats and kind loan
    r = cur({'id': 12, 'loan_parent': 3, 'stats': {'apps': 9, 'goals': 0}}, _stored((2023, 1003)))
    assert [(x['club'], x['kind'], x['apps'], x['season']) for x in r[1:]] == [('Parent FC', None, None, '2027/28'),
                                                                               ('B FC', 'loan', 9, '2027/28')], r
    assert not r[1]['current'] and r[2]['current']
    # youth / reserve array club, and contract club (employment value = club entity id = club id + 1: 3 -> B FC)
    assert cur({'id': 14}, _stored())[0]['club'] == 'A FC'
    assert cur({'id': 15}, _stored())[0]['club'] == 'B FC'
    # free agent: no club -> no row, empty state stays
    assert cur({'id': 99}, _stored()) == []
    assert len(cur({'id': 99}, _stored((2023, 1001)))) == 1
    # season rollover is July 1st; calendar-year nations use the calendar year
    for ref, want in (('2027-07-01', '2027/28'), ('2027-06-30', '2026/27'), ('2028-12-31', '2028/29')):
        set_ref(ref)
        assert cur({'id': 10}, _stored())[0]['season'] == want, (ref, want)
    set_ref('2028-01-02')
    assert cur({'id': 16}, _stored())[0]['season'] == '2028', 'calendar-year league'
    # end to end: no install DB -> status stays no_install but the current club row is there
    real = H.install_db_dir
    H.install_db_dir = lambda *_a, **_k: None
    try:
        c = H.career_for_person({'id': 10}, sd)
    finally:
        H.install_db_dir = real
    assert c['status'] == 'no_install' and len(c['rows']) == 1 and c['rows'][0]['club'] == 'A FC', c
    set_ref(datetime.date(2024, 7, 1))
    print('ok: current season row (young one-club, missing club, loan, no duplicate, free agent, sources, season label)')


def _psh_rows(spec):
    """Synthetic player_stats_hist: spec = [(team, year, flag, apps, goals, j23)] -> (dt, row index list)."""
    import struct
    dt = bytearray(8)
    for team, year, flag, apps, goals, j23 in spec:
        r = bytearray(152)
        struct.pack_into('<I', r, 1, team)
        struct.pack_into('<H', r, 11, year)
        r[23], r[24], r[26], r[27], r[31] = j23, apps, apps, goals, flag
        dt += r
    return bytes(dt)


def _psh_ls(entries):
    import struct
    out = bytearray(8) + struct.pack('<II', 0, len(entries))
    for e in entries:                               # e = row indexes; the odd positions are filler (rel offsets)
        vals = []
        for i, r in enumerate(e):
            vals += [r * 152] + ([152 * (i + 1)] if i < len(e) - 1 else [])
        out += struct.pack('<I', len(vals)) + struct.pack('<%dI' % len(vals), *vals)
    return bytes(out)


def test_psh_ties():
    """Person -> stats-history groups: the first pointer is exact, later pointers are stale and only a window that the
    carry-over byte (+23 = apps of the previous club in the same competition class) resolves."""
    from fm_editor import history as H
    rows = [
        (10, 2026, 1, 18, 4, 0), (10, 2026, 0, 7, 3, 0), (10, 2026, 4, 3, 0, 0),             # 0-2   slot 0: club 10 (f1 18, f4 3)
        (20, 2026, 1, 30, 2, 0), (20, 2026, 2, 4, 0, 0),                                      # 3-4   an earlier joiner of club 20
        (20, 2026, 1, 9, 1, 18), (20, 2026, 2, 5, 0, 0), (20, 2026, 4, 2, 0, 12),             # 5-7   joiner with f1 18 + f4 12
        (20, 2026, 1, 16, 6, 18), (20, 2026, 2, 7, 2, 0), (20, 2026, 4, 5, 1, 3),             # 8-10  joiner with f1 18 + f4 3
        (20, 2026, 1, 3, 1, 18), (20, 2026, 0, 1, 0, 0),                                      # 11-12 one check only (f1 18)
        (11, 2026, 1, 18, 0, 0), (11, 2026, 4, 12, 0, 0),                                     # 13-14 slot 1: club 11 (f1 18, f4 12)
        (30, 2026, 1, 20, 2, 0),                                                              # 15    slot 2: stays at club 30
        (31, 2023, 1, 0, 0, 0),                                                               # 16    a 2023 stub
        (12, 2026, 1, 18, 1, 0), (12, 2026, 4, 3, 0, 0),                                      # 17-18 slot 4: same evidence as slot 0
    ]
    dt = _psh_rows(rows)
    # slot 0 / 1 point into club 20's block (row 4, stale); the carry-over picks 8 (f1 18 + f4 3) / 5 (f1 18 + f4 12)
    ls = _psh_ls([[0, 4], [13, 4], [15], [16, 15]])
    psh = H.Psh(dt, ls)
    assert psh.ties == {0: [8], 1: [5]}, psh.ties
    g = psh.groups(0)
    assert [(x['row'], x['tier'], x['apps'], x['goals']) for x in g] == [(0, 1, 18, 4), (8, 2, 16, 6)], g
    assert [(x['row'], x['tier']) for x in psh.groups(1)] == [(13, 1), (5, 2)]
    assert [x['row'] for x in psh.groups(2)] == [15] and psh.groups(3) == [] and psh.groups(99) == []
    # two slots with the same evidence both wanting group 8 -> dropped for both (no guessing)
    psh2 = H.Psh(dt, _psh_ls([[0, 4], [13, 4], [15], [16], [17, 4]]))
    assert psh2.ties == {1: [5]}, psh2.ties
    # equal evidence for two candidates -> nothing tied
    rows2 = rows[:8] + [(20, 2026, 1, 16, 6, 18), (20, 2026, 1, 15, 5, 18)] + rows[11:]
    psh3 = H.Psh(_psh_rows(rows2), _psh_ls([[0, 4]]))
    assert 0 not in psh3.ties or psh3.ties[0] != [8], psh3.ties
    print('ok: stats history ties (exact first group, carry-over window, conflicts, equal evidence, stub)')


def test_fee_to_buyer():
    """The save keeps a fee on the selling club's row, the game shows it on the club joined (same or next season)."""
    from fm_editor import history as H
    r = lambda y, c, fee=None, **k: {'year': y, 'club_uid': c, 'fee': fee, **k}
    rows = [r(2021, 1, 3_000_000), r(2021, 2), r(2022, 2, 34_000_000), r(2023, 3), r(2024, 3, 5_000_000),
            r(2026, 4, 50_000_000, from_stats=True), r(2027, 5)]
    H._fee_to_buyer(rows)
    assert [x['fee'] for x in rows] == [None, 3_000_000, None, 34_000_000, None, None, None], rows   # 2026 -> 2027 gap not allowed
    rows = [r(2026, 4, 98_000_000, from_stats=True), r(2026, 5), r(2027, 5)]
    H._fee_to_buyer(rows)
    assert [x['fee'] for x in rows] == [None, 98_000_000, None]
    print('ok: fee moves to the buying club row')


def test_totals():
    """Total row of the Career Stats table: sums of the recorded cells, rating weighted by apps, None = '-'."""
    from fm_editor import history as H
    rows = [{'fee': 98000000, 'apps': 16, 'goals': 6, 'assists': 2, 'pom': 1, 'rating': 7.15, 'rated': 16},
            {'fee': None, 'apps': 18, 'goals': 4, 'assists': 2, 'pom': 0, 'rating': 6.98, 'rated': 18},
            {'fee': None, 'apps': 35, 'goals': 6, 'assists': None, 'pom': None, 'rating': None, 'rated': None}]
    assert H.career_totals(rows) == {'fee': 98000000, 'apps': 69, 'goals': 16, 'assists': 4, 'pom': 1, 'avg': 7.06}
    assert H.career_totals([{'apps': None, 'goals': None}]) == {'fee': None, 'apps': None, 'goals': None,
                                                                'assists': None, 'pom': None, 'avg': None}
    assert H.COMP_NAMES[11] == 'Premier Division' and H.COMP_NAMES[32] == 'Serie A'
    print('ok: career totals')


def test_real_counts():
    """Real snapshot: counts before (stored rows only) / after (with the current row) on every 20th player."""
    import pickle
    from fm_editor import history as H
    from fm_editor.agecalc import set_ref
    from fm_editor.archive import parse_archive
    from PyQt6.QtCore import QCoreApplication
    from gui.workers import ParseWorker
    _app = QCoreApplication.instance() or QCoreApplication([])
    res = {}
    w = ParseWorker(SAVE, use_cache=False)
    w.done.connect(res.update)
    w.run()
    assert res, 'parse failed'
    set_ref(res['save_info']['in_game_date'])
    _h, members, *_r = parse_archive(SAVE)
    sd = {k: res[k] for k in ('clubs', 'squads', 'sub_squads', 'employment', 'b')}
    sd.update(save_path=SAVE, members=members)
    pl = [p for p in res['people'] if p.get('ca') is not None]
    by_id = {p['id']: p for p in pl}
    sample = pl[::20]
    n = len(sample)
    stored_rows = shown_rows = club = club_empty_before = 0
    for p in sample:
        c = H.career_for_person(p, sd)
        cur, _par = H.current_clubs(p, sd)
        stored = [r for r in c['rows'] if not r['current'] and not r.get('parent') and not r.get('from_stats')]
        stored_rows += bool(stored)
        shown_rows += bool(c['rows'])
        if cur is not None:
            club += 1
            club_empty_before += not stored
            assert c['rows'] and c['rows'][-1]['current'] and c['rows'][-1]['club_uid'] == cur['uid'], p['name']
            assert [r['season'] for r in c['rows']].count(c['rows'][-1]['season']) <= 2
        else:
            assert not any(r['current'] for r in c['rows'])
    print(f'snapshot sample 1/20 ({n} players): history rows before {stored_rows} ({100 * stored_rows / n:.1f}%), '
          f'after {shown_rows} ({100 * shown_rows / n:.1f}%); players with a club {club}, of them empty before {club_empty_before}, after 0')
    assert shown_rows > stored_rows
    # pinned examples: a newgen with no stored history (one row), a loanee, a Spurs regular
    carb = H.career_for_person(by_id[131586], sd)             # Marco Carbonero (generated uid > install DB max)
    assert carb['status'] == 'none' and [(r['season'], r['club'], r['kind']) for r in carb['rows']] == [('2027/28', 'U.B. Conquense', None)], carb
    loan = H.career_for_person(by_id[177303], sd)             # Nicolás Vázquez: Astur C.F. on loan from Real Oviedo
    assert [(r['club'], r['kind']) for r in loan['rows']] == [('Real Oviedo', None), ('Astur C.F.', 'loan')], loan['rows']
    vdv = H.career_for_person(by_id[39811], sd)               # Micky van de Ven: stored rows + the current Spurs season
    last = vdv['rows'][-1]
    assert (last['season'], last['club'], last['apps'], last['goals']) == ('2027/28', 'Tottenham Hotspur', 28, 2), last
    # Info (fee) is shown on the row of the club JOINED: Volendam -> Wolfsburg 3.0M, Wolfsburg -> Spurs 34.3M
    fees = [(r['season'], r['club'], r['fee']) for r in vdv['rows'] if r['fee']]
    assert fees == [('2021/22', 'VfL Wolfsburg', 3007955), ('2023/24', 'Tottenham Hotspur', 34298584)], fees
    assert (last['assists'], last['pom'], last['rating'], last['division']) == (2, 0, 7.01, 'Premier Division'), last
    # Nico Paz (in-game Career Stats, 9 Feb 2028): the past rows the save reproduces (league apps/goals + division name)
    paz = H.career_for_person(by_id[101766], sd)
    assert [(r['season'], r['club'], r['division'], r['apps'], r['goals'], r['assists'], r['pom'], r['rating'])
            for r in paz['rows'][1:5]] == [
        ('2021/22', 'Real Madrid Castilla C.F.', 'Spanish Federation 1B', 6, 0, None, None, None),
        ('2022/23', 'Real Madrid Castilla C.F.', 'Spanish Federation 1A', 14, 1, None, None, None),
        ('2023/24', 'Real Madrid C.F.', 'First Division', 4, 0, None, None, None),
        ('2024/25', 'Como 1907', 'Serie A', 35, 6, None, None, None)], paz['rows']
    cur = paz['rows'][-1]       # snapshot (2 Jan 2028): all-competition season stats, same fields as the squad screen
    assert (cur['assists'], cur['pom'], cur['rating'], cur['division']) == (5, 4, 7.58, 'Premier Division'), cur
    # the game's 2026/27 rows come from player_stats_hist_dt.cmt (tied to the person through the game_db slot, see the
    # `Psh` docs): Como 18 4 2 0 6.98, Tottenham 16 6 2 1 7.15 with the 97.9M fee shown as £98M on the Tottenham row
    assert [(r['season'], r['club'], r['division'], r['apps'], r['goals'], r['assists'], r['pom'], r['rating'], r['fee'])
            for r in paz['rows'][5:7]] == [
        ('2026/27', 'Como 1907', 'Serie A', 18, 4, 2, 0, 6.98, None),
        ('2026/27', 'Tottenham Hotspur', 'Premier Division', 16, 6, 2, 1, 7.15, 97911664)], paz['rows']
    assert len(paz['rows']) == 8 and paz['rows'][0]['season'] == '2020/21' and paz['rows'][0]['apps'] == 0
    from gui.player_window import PlayerWindow as _PW
    assert _PW._fmt_fee(97911664) == '£98M' and _PW._fmt_fee(34298584) == '£34M' and _PW._fmt_fee(3007955) == '£3M'
    # tier 1 (first group of a person = exact) for the Spurs 2026/27 squad (slots 51378-51391), pinned values
    def past(pid):
        c = H.career_for_person(by_id[pid], sd)
        return [(r['season'], r['club'], r['division'], r['apps'], r['goals'], r['assists'], r['pom'], r['rating'], r['fee'])
                for r in c['rows'] if r.get('from_stats')]
    sp = 'Tottenham Hotspur'
    assert past(39811) == [('2026/27', sp, 'Premier Division', 35, 2, 1, 0, 7.1, None)]          # van de Ven
    assert past(61914) == [('2026/27', sp, 'Premier Division', 30, 2, 20, 5, 7.49, None)]        # Porro
    assert past(44427) == [('2026/27', sp, 'Premier Division', 34, 2, 3, 0, 6.91, None)]         # Tonali
    # tier 2 (movers inside 2026/27, tied by the carry-over byte: the new group's +23 = apps at the old club in the
    # same competition class, matched on two classes each): 7 players of 14 clubs / 8 nations; the old group is the
    # exact first pointer, so the match also confirms it
    movers = {
        45951: [('2026/27', 'Atalanta Bergamasca Calcio', 'Serie A', 18, 0, 3, 1, 6.77, None),
                ('2026/27', sp, 'Premier Division', 16, 1, 1, 0, 6.99, 80116248)],            # Scalvini
        46781: [('2026/27', 'Brighton & Hove Albion', 'Premier Division', 19, 5, 6, 1, 7.06, None),
                ('2026/27', 'Liverpool', 'Premier Division', 15, 2, 1, 1, 6.92, 19485783)],   # Mitoma
        88198: [('2026/27', 'Girona F.C.', None, 19, 4, 6, 7, 7.68, None),
                ('2026/27', 'Manchester United', 'Premier Division', 3, 0, 0, 0, 6.67, 29312666)],   # Asprilla
        78595: [('2026/27', 'FC Basel 1893', None, 19, 0, 1, 1, 6.92, None),
                ('2026/27', 'Olympique de Marseille', 'Ligue 1 Uber Eats', 5, 0, 1, 0, 6.8, 4387476)],   # Daniliuc
        93416: [('2026/27', 'Al-Hilal Saudi Football Club', 'Saudi Pro League', 3, 0, 0, 0, 6.7, None),
                ('2026/27', 'Al-Raed Saudi Football Club', None, 31, 2, 2, 3, 7.57, 0)],      # Al-Harbi (free)
        90002: [('2026/27', 'FC Red Bull Salzburg', None, 15, 0, 3, 2, 7.35, None),
                ('2026/27', 'VfB Stuttgart', 'Bundesliga', 11, 1, 2, 0, 6.96, 14514287)],     # Kratzig
        48086: [('2026/27', '1. FC Union Berlin', 'Bundesliga', 4, 0, 0, 0, 6.45, None),
                ('2026/27', 'FC Schalke 04', 'Bundesliga', 15, 0, 0, 0, 6.74, 3820640)],       # Nsoki
    }
    for pid, want in movers.items():
        assert past(pid) == want, (by_id[pid]['name'], past(pid))
    psh = H.psh_for(SAVE, members)
    assert len(psh.ents) == 86062 and len(psh.ties) == 1243 and len(psh.claimed) > 70000, (len(psh.ents), len(psh.ties))
    set_ref('2024-07-01')


def main():
    from fm_editor import history as H
    test_current_row()
    test_psh_ties()
    test_fee_to_buyer()
    test_totals()
    skip_if_missing()
    assert_snapshot(SAVE)
    if not H.install_db_dir(SAVE):
        print('SKIPPED (FM install database not found): test_history')
        return
    from fm_editor.archive import get_member, parse_archive
    from fm_editor.gamedb import find_names, find_people, match_identities
    _h, members, *_ = parse_archive(SAVE)
    b = get_member(SAVE, next(m for m in members if m['name'] == 'game_db.dat'))
    first, last, _ns, ne = find_names(b)
    people = find_people(b, first, last, ne)
    match_identities(b, people, ne)
    by_id = {p['id']: p for p in people}
    # person_uid (local scan) == match_identities for the people we use
    for pid, (uid, name) in {**PLAYERS, **STAFF}.items():
        assert by_id[pid]['uid'] == uid, name
        assert H.person_uid(b, by_id[pid]) == uid, name

    ph = {pid: H.player_history(uid, SAVE, members) for pid, (uid, _n) in PLAYERS.items()}
    kane = ph[32446]
    rows = kane['rows']
    assert kane['n_install'] == 18 and len(rows) == 20
    assert (rows[2]['year'], rows[2]['kind'], rows[2]['apps'], rows[2]['goals']) == (2010, 'loan', 18, 5)   # Orient
    assert (rows[4]['year'], rows[4]['kind'], rows[4]['apps'], rows[4]['goals']) == (2011, 'loan', 22, 7)   # Millwall
    assert (rows[9]['year'], rows[9]['apps'], rows[9]['goals']) == (2014, 34, 21)
    assert rows[17]['fee'] == 85746464 and (rows[18]['apps'], rows[18]['goals']) == (32, 36)             # Bayern 23/24
    assert ph[33096]['rows'][7]['fee'] == 100000000 and ph[33096]['rows'][8]['apps'] == 38          # Rice -> Arsenal
    assert any(r['kind'] == 'loan' and (r['apps'], r['goals']) == (37, 5) for r in ph[32666]['rows'])  # Notts County
    assert ph[39811]['rows'][7]['fee'] == 34298584                                                       # Wolfsburg

    # club resolution: the field is the uid after the club (predecessor rule)
    d = H.install_db_dir(SAVE)
    uids, names, _nats = H.install_clubs(d)
    cl = H.Clubs([], d)
    assert len(uids) > 50000
    want = {2: 'Leyton Orient', 4: 'Millwall', 6: 'Norwich City', 7: 'Leicester City', 17: 'Tottenham Hotspur',
            18: 'FC Bayern München'}
    for i, nm in want.items():
        assert cl.lookup(rows[i]['club_raw'])[1] == nm, (i, cl.lookup(rows[i]['club_raw']))

    def career(pid):
        uid, _n = STAFF[pid]
        return [(r['job'], cl.lookup(r['club_raw'])[0], (r['start'] or (0,))[0], (r['end'] or (0,))[0])
                for r in H.staff_history(uid, SAVE, members)['rows']]
    pep = career(127)
    assert ('Manager', 1707, 2008, 2012) in pep and ('Manager', 678, 2016, 0) in pep   # Barcelona, Man City
    assert ('Player', 1112, 2001, 2002) in pep                           # Brescia: needs the install club list
    assert ('Manager', 727, 2014, 2019) in career(362)                   # Pochettino at Spurs
    assert ('Manager', 629, 2004, 2007) in career(10510) and ('Manager', 679, 2016, 2018) in career(10510)
    assert ('Manager', 601, 2019, 0) in career(13654)                    # Arteta at Arsenal
    # the human manager (created in game) has no history
    assert H.staff_history(by_id[168978]['uid'], SAVE, members) is None
    print('ok: history rows, fees, loans, save continuation, club resolution, staff careers')
    test_real_counts()


if __name__ == '__main__':
    main()
