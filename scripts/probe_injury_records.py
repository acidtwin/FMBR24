"""Probe b11=0x47 records for squad players to identify injury record format.

Usage:
    python scripts/probe_injury_records.py /path/to/save.fm <club_name>

Example:
    python scripts/probe_injury_records.py save.fm "Tottenham"

Prints every b11=0x47 linked record found for each squad player, showing
b10 and trail bytes so we can identify the actual injury discriminator.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fm_editor.archive import parse_archive, get_member
from fm_editor.gamedb import find_names, find_clubs, find_squads, find_people, find_abilities, match_identities


def probe(save_path, club_filter):
    print(f"Loading {save_path}...")
    header, members, *_ = parse_archive(save_path)
    gdb_ref = next((m for m in members if m['name'] == 'game_db.dat'), None)
    if not gdb_ref:
        print("game_db.dat not found"); return

    b = bytearray(get_member(save_path, gdb_ref))
    first_names, last_names, names_start, names_end = find_names(b)
    clubs = find_clubs(b, names_start)
    squads, _ = find_squads(b, clubs, names_start)
    people = find_people(b, first_names, last_names, names_end)
    match_identities(b, people, names_end)
    abilities = find_abilities(b, names_end)
    player_ids = set(abilities.keys())

    # Find the club
    club = next((c for c in clubs if club_filter.lower() in c['name'].lower()), None)
    if not club:
        print(f"Club '{club_filter}' not found. Available: {[c['name'] for c in clubs[:20]]}")
        return

    squad_pids = set(squads.get(club['id'], []))
    players = [p for p in people if p.get('id') in squad_pids and p.get('id') in player_ids]
    pid_to_person = {p['id']: p for p in people}

    print(f"\nClub: {club['name']}  Squad size: {len(players)}\n")
    print(f"{'Name':<30} {'id':>8}  {'b10':>4} {'b11':>4} {'trail':>20}  days_at_+12")
    print('-' * 80)

    found_0x47 = 0
    for p in sorted(players, key=lambda x: x.get('name', '')):
        end = p['end']
        count = b[end + 34] if end + 34 < len(b) else 0
        for k in range(min(count, 60)):
            roff = end + 35 + k * 16
            if roff + 16 > len(b):
                break
            if b[roff + 11] == 0x47:
                b10 = b[roff + 10]
                trail = b[roff + 12:roff + 16].hex(' ')
                days = b[roff + 12]
                print(f"{p['name']:<30} {p['id']:>8}  0x{b10:02x} 0x47  {trail:>20}  {days}")
                found_0x47 += 1

    print(f"\nTotal 0x47 records found: {found_0x47} across {len(players)} players")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    probe(sys.argv[1], sys.argv[2])
