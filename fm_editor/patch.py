"""HGP and HGC detection and patching for FM24 save files.

HGP = Homegrown Player (nation-level): b10=0x08, b11=0x46, bytes 0-3 = England (0x8b).
HGC = Homegrown at Club: b10=0x01, b11=0x48, bytes 0-3 = club entity ID.
Club entity ID is found from b11=0x6a (employment) records — typically club_id+1.

HGP patch strategy:
  1. If a b11=0x40 non-HGP override flag exists: flip b11 to 0x47.
  2. If a b11=0x46 record exists with non-England nation: rewrite first 4 bytes to England (in place).
  3. A player with NO b11=0x46 record at all (never qualified in any nation, e.g. a foreign signing; 55k of
     128k players in a real save) has nothing to rewrite: insert a new 16-byte England record (size change,
     same insert rule as HGC; 4,253 players carry exactly this record in the game's own data).

HGC patch strategy: overwrite first b11=0x48 record's entity bytes; if none exists,
insert a new 16-byte record (size change). Process people in descending end-offset
order when insertions may occur, so earlier offsets stay valid.
"""

ENGLAND_NATION_ID = 0x8b  # 139

_HGC_RECORD_TEMPLATE = bytearray([
    0, 0, 0, 0,       # bytes 0-3: club entity ID (little-endian), filled in
    0, 0, 0, 0,       # bytes 4-7: zeroes
    0, 0,             # bytes 8-9: zeroes
    0x01, 0x48,       # b10=0x01, b11=0x48
    0x01, 0xff, 0x00, 0xff,  # bytes 12-15
])


_HGP_RECORD_TEMPLATE = bytearray([
    ENGLAND_NATION_ID, 0, 0, 0,  # bytes 0-3: nation entity ID (England), little-endian
    0, 0, 0, 0,       # bytes 4-7: zeroes
    0, 0,             # bytes 8-9: zeroes
    0x08, 0x46,       # b10=0x08, b11=0x46
    0x01, 0xff, 0x00, 0xff,  # bytes 12-15 (same as the game's own England records)
])


def is_homegrown(b, person):
    end = person['end']
    if end + 35 > len(b): return False
    count = b[end + 34]
    for k in range(min(count, 40)):
        roff = end + 35 + k * 16
        if roff + 16 > len(b): break
        if (b[roff:roff + 4] == b'\x8b\x00\x00\x00'
                and b[roff + 10] == 0x08
                and b[roff + 11] == 0x46):
            return True
    return False


def patch_to_homegrown(b, person):
    """Patch person in bytearray b to be HGP. Return True if changed."""
    end = person['end']
    if end + 35 > len(b): return False
    count = b[end + 34]
    patched = False
    for k in range(min(count, 40)):
        roff = end + 35 + k * 16
        if roff + 16 > len(b): break
        b10, b11 = b[roff + 10], b[roff + 11]
        if b10 == 0x00 and b11 == 0x40:
            # (injuries are read from injury_manager.dat, not from this record type)
            b[roff + 11] = 0x47
        if b10 == 0x08 and b11 == 0x46 and b[roff] != ENGLAND_NATION_ID:
            b[roff] = ENGLAND_NATION_ID
            b[roff + 1] = 0x00
            b[roff + 2] = 0x00
            b[roff + 3] = 0x00
            patched = True
    return patched


def insert_hgp_record(b, person):
    """Append a new England 0x46 record to a person who has none (size +16). Callers sort persons by
    person['end'] DESCENDING, like patch_to_hgc. Returns True if inserted."""
    end = person['end']
    if end + 35 > len(b): return False
    rec_count = b[end + 34]
    if rec_count >= 255:  # count byte is full: inserting would corrupt the record block
        return False
    insert_at = end + 35 + rec_count * 16
    b[insert_at:insert_at] = _HGP_RECORD_TEMPLATE
    b[end + 34] += 1
    return True


def find_club_entity_id(b, squad):
    """Return the club entity ID by finding the most common val0 in b11=0x6a records."""
    counts = {}
    for person in squad:
        end = person['end']
        if end + 35 > len(b): continue
        count = b[end + 34]
        seen = set()
        for k in range(min(count, 40)):
            roff = end + 35 + k * 16
            if roff + 16 > len(b): break
            if b[roff + 10] == 0x01 and b[roff + 11] == 0x6a:
                val = int.from_bytes(b[roff:roff + 4], 'little')
                if val not in seen:
                    counts[val] = counts.get(val, 0) + 1
                    seen.add(val)
    return max(counts, key=counts.get) if counts else None


def is_hgc(b, person, club_entity_id):
    """Return True if person has HGC status for club_entity_id."""
    end = person['end']
    if end + 35 > len(b): return False
    count = b[end + 34]
    for k in range(min(count, 40)):
        roff = end + 35 + k * 16
        if roff + 16 > len(b): break
        if b[roff + 10] == 0x01 and b[roff + 11] == 0x48:
            if int.from_bytes(b[roff:roff + 4], 'little') == club_entity_id:
                return True
    return False


def patch_to_hgc(b, persons_desc, club_entity_id):
    """Patch list of persons to HGC for club_entity_id.

    persons_desc must be sorted by person['end'] DESCENDING so that insertions
    (when a player has no existing b11=0x48 record) don't invalidate earlier offsets.

    Returns count of persons actually changed.
    """
    changed = 0
    for person in persons_desc:
        end = person['end']
        if end + 35 > len(b): continue
        rec_count = b[end + 34]
        first_48_roff = None
        already = False
        for k in range(min(rec_count, 40)):
            roff = end + 35 + k * 16
            if roff + 16 > len(b): break
            if b[roff + 10] == 0x01 and b[roff + 11] == 0x48:
                if int.from_bytes(b[roff:roff + 4], 'little') == club_entity_id:
                    already = True
                    break
                if first_48_roff is None:
                    first_48_roff = roff
        if already:
            continue
        if first_48_roff is not None:
            b[first_48_roff:first_48_roff + 4] = club_entity_id.to_bytes(4, 'little')
        else:
            if rec_count >= 255:  # count byte is full: inserting would corrupt the record block
                continue
            insert_at = end + 35 + rec_count * 16
            new_rec = bytearray(_HGC_RECORD_TEMPLATE)
            new_rec[0:4] = club_entity_id.to_bytes(4, 'little')
            b[insert_at:insert_at] = new_rec
            b[end + 34] += 1
        changed += 1
    return changed


def hgp_in_place(b, people):
    """HGP for each person, in place (offsets stay valid). Returns the list of persons whose bytes changed."""
    def recs(p):
        e = p['end']
        return bytes(b[e + 35:e + 35 + 16 * min(b[e + 34], 40)])
    out = []
    for p in people:
        before = recs(p)
        patch_to_homegrown(b, p)
        if before != recs(p):
            out.append(p)
    return out


def apply_queue(b, queue, entity_of):
    """Write queued homegrown changes into bytearray b in the SAFE order (offsets are the ones parsed at load).
    queue: iterable of (person, 'hgp'|'hgc'); entity_of(person) -> club entity id or None.
    1. every HGP that has a 0x46 record to rewrite, in place (offsets stay valid),
    2. inserts (HGC record, or an HGP record for a person with no 0x46 at all) for persons sorted by record
       offset DESCENDING (a 16-byte insert only shifts later bytes). Only the part a person is missing is added.
    Returns (changed_hgp, changed_hgc). Raises on any failure: the caller keeps a pristine copy of b."""
    hgp, hgc = {}, {}
    for p, kind in queue:
        (hgp if kind == 'hgp' else hgc)[id(p)] = p
    changed = {id(p) for p in hgp_in_place(b, [p for p in hgp.values() if not is_homegrown(b, p)])}
    todo = {}  # id(person) -> [person, club entity or None, needs an HGP record inserted]
    for p in hgp.values():
        if not is_homegrown(b, p):  # still not HGP after the in-place pass: no 0x46 record exists
            todo[id(p)] = [p, None, True]
    for p in hgc.values():
        ent = entity_of(p)
        if ent is not None and not is_hgc(b, p, ent):
            todo.setdefault(id(p), [p, None, False])[1] = ent
    n_hgc = 0
    for p, ent, need_hgp in sorted(todo.values(), key=lambda t: t[0]['end'], reverse=True):
        if need_hgp and insert_hgp_record(b, p):
            changed.add(id(p))
        if ent is not None:
            n_hgc += patch_to_hgc(b, [p], ent)
    return len(changed), n_hgc
