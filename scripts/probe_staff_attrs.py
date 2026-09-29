"""Probe FM24 binary for staff job role, coaching qualifications, and coaching attributes.

Usage:
    python scripts/probe_staff_attrs.py /path/to/save.fm [name_filter]

name_filter: case-insensitive substring to filter staff names (default: all staff).
Example: python scripts/probe_staff_attrs.py save.fm "Baldini"

Output shows, for each staff person:
  - end+25..end+33  (9 bytes) — likely coaching qualification / unknown
  - b8 value of each linked record by b11 type
  - 64 bytes after last linked record (likely coaching attributes region)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fm_editor.archive import parse_archive, get_member
from fm_editor.gamedb import find_names, find_clubs, find_people, find_abilities, match_identities


def _u32(b, i):
    return int.from_bytes(b[i:i+4], 'little')


def probe(save_path, name_filter=''):
    print(f"Loading {save_path}...")
    header, members, index_marker, archive_name, subdir_count, subdirs = \
        parse_archive(save_path)
    gdb_ref = next((m for m in members if m['name'] == 'game_db.dat'), None)
    if not gdb_ref:
        print("game_db.dat not found"); return

    b = bytearray(get_member(save_path, gdb_ref))
    first_names, last_names, names_start, names_end = find_names(b)
    clubs = find_clubs(b, names_start)
    people = find_people(b, first_names, last_names, names_end)
    abilities = find_abilities(b, names_end)
    match_identities(b, people, names_end)

    player_ids = set(abilities.keys())
    staff = [p for p in people if p.get('id', -1) not in player_ids
             and p.get('id', -1) >= 0]

    if name_filter:
        staff = [p for p in staff if name_filter.lower() in p.get('name', '').lower()]
        print(f"Filtered to {len(staff)} staff matching '{name_filter}'")
    else:
        print(f"Total staff: {len(staff)} (showing first 20)")
        staff = staff[:20]

    for p in staff:
        end = p['end']
        name = p['name']
        pid = p['id']

        # Count of linked records
        count = b[end + 34] if end + 34 < len(b) else 0
        records_end = end + 35 + count * 16

        print(f"\n{'='*60}")
        print(f"  {name}  (id={pid})")
        print(f"  end={end}  linked_count={count}  records_end={records_end}")

        # Region end+4..8 (5 unknown bytes)
        gap1 = b[end+4:end+9] if end+9 <= len(b) else b''
        print(f"  end+4..8   (5 bytes): {gap1.hex(' ')}")

        # Region end+25..33 (9 unknown bytes — likely qualifications)
        gap2 = b[end+25:end+34] if end+34 <= len(b) else b''
        print(f"  end+25..33 (9 bytes): {gap2.hex(' ')}")

        # All linked records — dump b8, b9, b10, b11 and first 4 bytes
        print(f"  Linked records ({count}):")
        for k in range(min(count, 20)):
            roff = end + 35 + k * 16
            if roff + 16 > len(b):
                break
            data  = _u32(b, roff)
            d4    = b[roff+4:roff+8].hex(' ')
            b8    = b[roff+8]
            b9    = b[roff+9]
            b10   = b[roff+10]
            b11   = b[roff+11]
            trail = b[roff+12:roff+16].hex(' ')
            print(f"    [{k:2d}] data={data:10d}  mid={d4}  b8={b8:02x} b9={b9:02x}  "
                  f"b10={b10:02x} b11={b11:02x}  trail={trail}")

        # Find the coaching data block: magic = 60 1a ea 07
        # Located at records_end + (10 if count > 0 else 0)
        magic_offset = records_end + (10 if count > 0 else 0)
        # Magic varies per save (first byte differs: 0x60 or 0xc2 etc.)
        MAGIC_SUFFIX = b'\x1a\xea\x07'
        magic_found = False
        for check_off in [magic_offset] + list(range(records_end - 10, records_end + 60)):
            if b[check_off+1:check_off+4] == MAGIC_SUFFIX:
                m = check_off
                magic_found = True
                break
        # Print 30 bytes before magic (between records_end and magic)
        pre_gap = b[records_end:records_end+30] if magic_found else b''
        if magic_found:
            pre_gap = b[records_end:m]
        if pre_gap:
            print(f"  Pre-magic gap ({len(pre_gap)} bytes): {pre_gap.hex(' ')}")

        if magic_found:
            pid_check = _u32(b, m + 12) & 0xFFFF
            print(f"  Coaching block at +{m - end} from end  magic={b[m:m+4].hex(' ')}  pid_check={pid_check} vs id={pid}")
            # Dump full block +0..+300 for analysis
            block = bytes(b[m:m+300])
            print(f"  Block +0..+300 hex: {block.hex(' ')}")
            attrs_raw = list(b[m+37:m+37+44])
            attrs_scaled = [max(1, min(20, round(v/5))) for v in attrs_raw]
            print(f"  Attrs raw (+37, 44): {attrs_raw}")
            print(f"  Attrs ÷5           : {attrs_scaled}")
            # Look for second coaching block around end+1000..+1400
            print(f"  Extended region end+1000..+1400:")
            chunk = bytes(b[end+1000:end+1400])
            print(f"    {chunk.hex(' ')}")
            # Look for magic suffix in that region
            for i in range(len(chunk)-4):
                if chunk[i+1:i+4] == b'\x1a\xea\x07':
                    print(f"    *** Magic at end+{1000+i}: {chunk[i:i+4].hex(' ')}")
            # Also scan for JPA/JSA linked records (b11=02 or similar)
            print(f"  Bytes end+200..+350 (post-block):  {bytes(b[end+200:end+350]).hex(' ')}")
            # Also print Section B candidates (bytes before first ff ff ff ff after magic+80)
            secb_start = m + 81
            secb = []
            for i in range(secb_start, min(secb_start + 30, len(b))):
                if b[i:i+4] == b'\xff\xff\xff\xff':
                    break
                secb.append(b[i])
            print(f"  Section B ({len(secb)} bytes): {bytes(secb).hex(' ')}  ÷5: {[max(1,min(20,round(v/5))) for v in secb]}")
        else:
            post = b[records_end:records_end+80]
            print(f"  No magic found. Post-records +80: {post.hex(' ')}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    save_path = sys.argv[1]
    name_filter = sys.argv[2] if len(sys.argv) > 2 else ''
    probe(save_path, name_filter)
