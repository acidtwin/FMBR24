"""Parse game_db.dat: name pools, clubs, squad memberships, people, identities."""
import struct


def _u16(b, p): return struct.unpack_from('<H', b, p)[0]
def _u32(b, p): return struct.unpack_from('<I', b, p)[0]


# -- Name pools ----------------------------------------------------------------

def _read_pool(b, start):
    if start + 16 >= len(b): return None, start
    count = _u32(b, start)
    if not (1 <= count <= 3_000_000): return None, start
    names = []; p = start + 4
    for i in range(count):
        if p + 8 > len(b) or _u32(b, p) != i: return None, start
        n = _u32(b, p + 4)
        if n > 512 or p + 8 + n > len(b): return None, start
        names.append(b[p + 8:p + 8 + n].decode('utf-8', errors='replace'))
        p += 8 + n
    return names, p


def find_names(b):
    """Return (first_names, last_names, names_start, names_end)."""
    blen = len(b)
    search = 4
    while True:
        # Pattern: bytes [p+4:p+8] == 0x00000000; jump straight to zero runs.
        z = b.find(b'\x00\x00\x00\x00', search, blen - 40)
        if z < 0:
            break
        p = z - 4
        search = z + 1
        if p < 0:
            continue
        count = _u32(b, p)
        if not (10000 <= count <= 3_000_000):
            continue
        n = _u32(b, p + 8)
        if not (1 <= n <= 100) or p + 16 + n > blen or _u32(b, p + 12 + n) != 1:
            continue
        first, end = _read_pool(b, p)
        if not first:
            continue
        last, end = _read_pool(b, end)
        if not last or len(last) < 10000:
            continue
        _, end = _read_pool(b, end)
        if _ is None:
            continue
        return first, last, p, end
    raise RuntimeError("Name tables not found in game_db.dat")


# -- Clubs ---------------------------------------------------------------------

def find_clubs(b, names_start):
    """Return list of club dicts with id/uid/name/short/offset."""
    clubs = []
    # Search for the 0xFFFFFFFF pattern that sits at at+17; bytearray.find is C-level.
    search = 17
    while True:
        ff = b.find(b'\xff\xff\xff\xff', search, names_start)
        if ff < 0:
            break
        at = ff - 17
        search = ff + 1
        if at < 0 or at + 50 >= names_start:
            continue
        if b[at + 12]:
            continue
        nation = _u32(b, at + 13)
        if nation > 255 or _u32(b, at + 25) != nation:
            continue
        uid, cid = _u32(b, at + 4), _u32(b, at)
        if uid == 0 or uid == 0xFFFFFFFF or uid != _u32(b, at + 8) or cid > 100000:
            continue
        n = _u32(b, at + 39)
        if not (2 <= n <= 200) or at + 47 + n >= names_start:
            continue
        sn = _u32(b, at + 43 + n)
        if not (1 <= sn <= 100) or at + 47 + n + sn > names_start:
            continue
        name = b[at + 43:at + 43 + n].decode('utf-8', errors='replace')
        short = b[at + 47 + n:at + 47 + n + sn].decode('utf-8', errors='replace')
        clubs.append({'id': cid, 'uid': uid, 'name': name, 'short': short, 'offset': at})
        search = at + 47 + n + sn + 17  # skip past this record
    return clubs


# -- Squads --------------------------------------------------------------------

def find_squads(b, clubs, names_start):
    """Return (squads, sub_squads).

    squads: {person_id: club_id} for first-team (kind 100).
    sub_squads: {club_id: {kind: [person_ids]}} for youth/reserve (kinds 18-23).
    """
    club_by_id = {c['id']: c for c in clubs}
    squads = {}
    sub_squads = {}
    p = 4
    while p + 70 < names_start:
        at = p; p += 1
        if b[at + 26] != 10: continue
        if b[at + 4:at + 14] != b'\x00' * 10: continue
        owner = _u32(b, at); ordinal = _u32(b, at + 14); uid = _u32(b, at + 18)
        if owner > 100000 or ordinal > 500000 or uid == 0: continue
        club = None
        if owner in club_by_id and club_by_id[owner]['uid'] == uid:
            if _u32(b, at + 22) == uid:
                club = club_by_id[owner]
        if club is None:
            typed = (b[at - 4] == 1 and b[at - 2] == 0xFF and
                     b[at - 3] in (18, 19, 20, 21, 23, 100))
            if typed:
                oid = owner - 1 if b[at - 3] in (20, 23) else owner
                if oid in club_by_id:
                    club = club_by_id[oid]
        if club is None: continue
        limit = min(at + 10000, names_start)
        q = at + 30
        while True:
            q = b.find(b'\xff\xff\xff\xff', q, limit - 14)
            if q < 0:
                break
            count = _u16(b, q + 4)
            if not (1 <= count <= 150):
                q += 1; continue
            end_q = q + 6 + count * 4 + 8
            if end_q > limit:
                q += 1; continue
            ids = [_u32(b, q + 6 + k * 4) for k in range(count)]
            if len(set(ids)) != count or any(i > 3_000_000 for i in ids):
                q += 1; continue
            kind = b[at - 3] if b[at - 4] == 1 and b[at - 2] == 0xFF else 100
            if kind == 100:
                for pid in ids:
                    squads[pid] = club['id']
            else:
                cid = club['id']
                if cid not in sub_squads:
                    sub_squads[cid] = {}
                sub_squads[cid][kind] = ids
            break
    return squads, sub_squads


# -- People --------------------------------------------------------------------

def find_people(b, first_names, last_names, names_end):
    """Return list of person dicts with offset/end/name/nation/birth_year/id."""
    people = []; p = names_end
    while p < len(b) - 100:
        start = p; p += 1
        if b[start + 4] or b[start + 9] or b[start + 14] or b[start + 17] or b[start + 18]:
            continue
        f = _u32(b, start); l = _u32(b, start + 5); n = _u32(b, start + 15)
        if (f != 0xFFFFFFFF and f >= len(first_names)) or \
           (l != 0xFFFFFFFF and l >= len(last_names)) or n > 200: continue
        end = start + 19 + n
        if end + 45 > len(b): continue
        day = _u16(b, end); year = _u16(b, end + 2); nation = _u16(b, end + 9)
        if not (1 <= day <= 366) or not (1850 <= year <= 2300) or nation > 255: continue
        if b[end + 11:end + 17] != b'\x00' * 6: continue
        if not all(v <= 20 for v in b[end + 17:end + 25]): continue
        fn = b[start + 19:end].decode('utf-8', errors='replace')
        if any(ord(c) <= 0x1f or c == '?' for c in fn): continue
        fname = first_names[f] if f != 0xFFFFFFFF else ''
        lname = last_names[l] if l != 0xFFFFFFFF else ''
        name = f"{fname} {lname}".strip() or fn
        personality = list(b[end + 17:end + 25])  # adaptability,ambition,loyalty,pressure,professionalism,sportsmanship,temperament,controversy
        people.append({'offset': start, 'end': end, 'name': name,
                       'nation': nation, 'birth_year': year, 'id': -1,
                       'personality': personality})
        p = end + 25
    return people


POSITIONS = ['GK','SW','DL','DC','DR','DM','ML','MC','MR','AML','AMC','AMR','ST','WBL','WBR']


def find_abilities(b, names_end):
    """Return dict: person_id -> {ca, pa, positions, raw_attrs}.
    Uses FM-SaveLens-24's FM24 ability-block algorithm (u8 CA/PA, not u16).
    """
    abilities = {}
    blen = len(b)
    p = names_end + 57
    while p < blen - 54:
        at = p
        p += 1
        if b[at - 37] != 0 or b[at - 35] != 0:
            continue
        ca = b[at - 38]; pa = b[at - 36]
        if not (1 <= ca <= 200) or not (1 <= pa <= 200):
            continue
        positions = list(b[at - 15:at])
        if not all(1 <= v <= 20 for v in positions) or 20 not in positions:
            continue
        attrs = list(b[at:at + 54])
        if not all(1 <= v <= 100 for v in attrs):
            continue
        uid = _u32(b, at - 53); source = _u32(b, at - 49)
        if uid == 0 or uid == 0xFFFFFFFF or source == 0 or source == 0xFFFFFFFF:
            continue
        owner_id = _u32(b, at - 57) + 1
        if owner_id not in abilities:
            abilities[owner_id] = {'ca': ca, 'pa': pa, 'positions': positions, 'raw_attrs': attrs}
        p = at + 54
    return abilities


def find_employment(b, people):
    """Return {person_id: club_entity_id} for non-player staff.

    Covers two record types:
      b10=0x01, b11=0x6a — current club contract (player or staff)
      b10=0x01, b11=0x03, b8=0x04 — manager/head coach appointment (current)

    Note: b11=0x48 is the HGC (Homegrown at Club) training record — bytes 0-3
    are the training-club entity, NOT an employment link; excluded here.
    b10=0x01, b11=0x03, b8=0x02 records appear on ex-players' historical
    records and are false positives; also excluded.
    """
    result = {}
    for p in people:
        pid = p.get('id', -1)
        if pid == -1:
            continue
        end = p['end']
        if end + 35 > len(b):
            continue
        count = b[end + 34]
        for k in range(min(count, 60)):
            roff = end + 35 + k * 16
            if roff + 16 > len(b):
                break
            b10, b11 = b[roff + 10], b[roff + 11]
            if b10 == 0x01 and b11 == 0x6a:
                entity_id = int.from_bytes(b[roff:roff + 4], 'little')
                if entity_id > 0:
                    result[pid] = entity_id
                    break
            elif b10 == 0x01 and b11 == 0x03 and b[roff + 8] == 0x04:
                entity_id = int.from_bytes(b[roff:roff + 4], 'little')
                if entity_id > 0:
                    result[pid] = entity_id
                    break
    return result


def find_club_staff(b, clubs, people, abilities, names_start):
    """Return {club_id: [person_ids]} from each club's binary staff PID array.

    Pattern: b[count_pos-1]==0x00 (byte before count is zero).
    Bounds each scan to [club_offset, next_club_offset) using sorted order.
    Uses bytearray.find() for speed instead of byte-by-byte iteration.
    """
    non_ca_ids = set(p['id'] for p in people if p.get('id', -1) >= 0) - set(abilities.keys())
    if not non_ca_ids:
        return {}

    sorted_clubs = sorted(clubs, key=lambda c: c['offset'])
    result = {}

    for idx, c in enumerate(sorted_clubs):
        cid = c['id']
        scan_start = c['offset']
        scan_end = sorted_clubs[idx + 1]['offset'] if idx + 1 < len(sorted_clubs) else names_start
        scan_end = min(scan_end, names_start)

        if scan_end - scan_start < 10:
            continue

        staff_pids = []
        seen = set()
        pos = scan_start + 1

        while True:
            # Jump to next \x00 byte — this is b[count_pos-1]
            zero_pos = b.find(b'\x00', pos, scan_end - 2)
            if zero_pos < 0:
                break

            count = b[zero_pos + 1]  # count_pos = zero_pos + 1
            if not (8 <= count <= 250):
                pos = zero_pos + 1
                continue

            arr_start = zero_pos + 2
            arr_end = arr_start + count * 4
            if arr_end > scan_end:
                pos = zero_pos + 1
                continue

            # Quick reject: first PID must be a plausible person ID
            first_pid = _u32(b, arr_start)
            if first_pid > 5_000_000 or first_pid not in non_ca_ids:
                pos = zero_pos + 1
                continue

            pids = [_u32(b, arr_start + k * 4) for k in range(count)]
            if len(set(pids)) != count or any(pid > 5_000_000 for pid in pids):
                pos = zero_pos + 1
                continue

            valid = sum(1 for pid in pids if pid in non_ca_ids)
            if valid >= max(count * 0.6, 6):
                for pid in pids:
                    if pid not in seen:
                        seen.add(pid)
                        staff_pids.append(pid)
                # Back up 4 bytes: adjacent arrays share a zero byte
                # (high byte of last PID == 0x00 marks next array's count)
                pos = max(zero_pos + 1, arr_end - 4)
            else:
                pos = zero_pos + 1

        if staff_pids:
            result[cid] = staff_pids

    return result


def primary_position(positions):
    """Return POSITIONS abbreviation for the player's best position (highest rating)."""
    return POSITIONS[positions.index(max(positions))]


def match_identities(b, people, names_end):
    """Assign FM person IDs to each person dict in-place."""
    max_id = _u32(b, names_end) + 1
    identities = []
    blen = len(b)
    # bytearray.find to jump to positions where b[p-3:p] == 0x000000 (was byte-by-byte)
    search = names_end + 4  # b[p-3] starts at names_end+4 → p = names_end+7
    while True:
        z = b.find(b'\x00\x00\x00', search, blen - 15)
        if z < 0:
            break
        p = z + 3  # b[p-3]=b[p-2]=b[p-1]=0
        search = z + 1
        if p < names_end + 7 or p >= blen - 12:
            continue
        if (b[p - 7] & 7) > 2 or b[p - 4] not in (0, 1, 4, 5):
            continue
        pid = _u32(b, p); uid = _u32(b, p + 4)
        if pid >= max_id or uid == 0 or uid == 0xFFFFFFFF: continue
        if uid != _u32(b, p + 8):
            if p < 12: continue
            day = _u16(b, p - 12) & 511; year = _u16(b, p - 10); source = _u32(b, p + 8)
            if not (1 <= day <= 366) or not (1900 <= year <= 2300) or \
               b[p - 6] & 0x85 or not (b[p - 6] & 0x60) or \
               source < 1000 or source == 0xFFFFFFFF:
                continue
        if pid & 255 == 0 and uid & 255 == 0 and _u32(b, p + 5) == _u32(b, p + 9): continue
        identities.append((p, pid, uid))

    tails = []; indices = []; prev = [None] * len(identities)
    for i, (pos, pid, uid) in enumerate(identities):
        lo, hi = 0, len(tails)
        while lo < hi:
            mid = (lo + hi) // 2
            if tails[mid] < pid: lo = mid + 1
            else: hi = mid
        prev[i] = indices[lo - 1] if lo > 0 else None
        if lo == len(tails):
            tails.append(pid); indices.append(i)
        else:
            tails[lo] = pid; indices[lo] = i

    ordered = []
    ix = indices[-1] if indices else None
    while ix is not None:
        ordered.append(identities[ix])
        ix = prev[ix]
    ordered.reverse()

    j = 0
    for i, person in enumerate(people):
        end = people[i + 1]['offset'] if i + 1 < len(people) else len(b)
        while j < len(ordered) and ordered[j][0] < person['end'] + 25:
            j += 1
        if j < len(ordered) and ordered[j][0] < end:
            person['id'] = ordered[j][1]
            person['uid'] = ordered[j][2]
            person['identity_offset'] = ordered[j][0]


# -- Coaching attributes -------------------------------------------------------

# Section B layout (magic+81, 14 bytes, ÷5 scale).
# Positions confirmed against FM24 coaching screen (Daniele Baldini id=355).
# Positions marked ? are best-guess based on value matching.
_COACHING_B_LABELS = [
    'WwY',            # 0  confirmed
    'Motivating',     # 1  confirmed
    'Mental',         # 2  likely (same value as SetPieces for reference coach)
    'Determination',  # 3  confirmed
    'Technical',      # 4  confirmed
    'Set Pieces',     # 5  likely
    'Fitness',        # 6  confirmed
    'Attacking',      # 7  confirmed
    'Defending',      # 8  unconfirmed (save-dependent)
    'GK Shot Stop',   # 9  unconfirmed
    'People Mgt',     # 10 confirmed
    'Tact Knowledge', # 11 confirmed
    'Negotiating',    # 12 confirmed
    'GK Handling',    # 13 confirmed
]

# Section A extra positions (magic+37 base, ÷5 scale).
_COACHING_A_EXTRAS = {
    33: 'Tactical',   # confirmed: =16 for Baldini
    36: 'JPA',        # confirmed: =11 for Baldini
    39: 'JSA',        # confirmed: =11 for Baldini
}

_MAGIC_SUFFIX = b'\x1a\xea\x07'


def _find_coaching_magic(b, records_end):
    """Find the XX 1a ea 07 magic for a person's coaching block."""
    for check_off in range(records_end, min(records_end + 60, len(b) - 4)):
        if b[check_off + 1:check_off + 4] == _MAGIC_SUFFIX:
            return check_off
    return -1


def find_coaching_attrs(b, people, player_ids):
    """Parse coaching block for each non-player person; store 'coaching' dict in-place."""
    MAGIC_SUFFIX = _MAGIC_SUFFIX
    for p in people:
        if p.get('id', -1) in player_ids:
            continue
        end = p['end']
        if end + 45 > len(b):
            continue
        count = b[end + 34] if end + 34 < len(b) else 0
        records_end = end + 35 + count * 16
        m = _find_coaching_magic(b, records_end)
        if m < 0 or m + 95 > len(b):
            continue
        # Verify PID at magic+12
        pid_check = _u32(b, m + 12) & 0xFFFF
        if pid_check != (p.get('id', -1) & 0xFFFF):
            continue
        # Section B: 14 bytes at magic+81, stop at 0xff
        sec_b = []
        for i in range(m + 81, min(m + 95, len(b))):
            if b[i] == 0xff:
                break
            sec_b.append(b[i])
        coaching = {}
        for idx, label in enumerate(_COACHING_B_LABELS):
            if idx < len(sec_b):
                coaching[label] = max(1, min(20, round(sec_b[idx] / 5)))
        # Section A extras at specific positions
        sec_a_base = m + 37
        for a_idx, label in _COACHING_A_EXTRAS.items():
            pos = sec_a_base + a_idx
            if pos < len(b):
                coaching[label] = max(1, min(20, round(b[pos] / 5)))
        if coaching:
            p['coaching'] = coaching
