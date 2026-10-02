"""Career history (fm_editor/history.py). Ground truth = real careers (Kane, Rice, Grealish, van de Ven, Mbappe,
Pochettino, Guardiola, Mourinho, Arteta). Run directly: python3 tests/test_history.py (about 30 s; skips politely
when the save or the FM install database is absent)."""
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


def main():
    from fm_editor import history as H
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


if __name__ == '__main__':
    main()
