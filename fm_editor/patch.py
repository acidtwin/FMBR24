"""HGP and HGC detection and patching for FM24 save files.

HGP = Homegrown Player (nation-level): b10=0x08, b11=0x46, bytes 0-3 = England (0x8b).
HGC = Homegrown at Club: b10=0x01, b11=0x48, bytes 0-3 = club entity ID.
Club entity ID is found from b11=0x6a (employment) records — typically club_id+1.

HGP patch strategy: in-place only (no size change).
  1. If a b11=0x40 non-HGP override flag exists: flip b11 to 0x47.
  2. If a b11=0x46 record exists with non-England nation: rewrite first 4 bytes to England.

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
            b[roff + 11] = 0x47
        if b10 == 0x08 and b11 == 0x46 and b[roff] != ENGLAND_NATION_ID:
            b[roff] = ENGLAND_NATION_ID
            b[roff + 1] = 0x00
            b[roff + 2] = 0x00
            b[roff + 3] = 0x00
            patched = True
    return patched


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
            insert_at = end + 35 + rec_count * 16
            new_rec = bytearray(_HGC_RECORD_TEMPLATE)
            new_rec[0:4] = club_entity_id.to_bytes(4, 'little')
            b[insert_at:insert_at] = new_rec
            b[end + 34] += 1
        changed += 1
    return changed
