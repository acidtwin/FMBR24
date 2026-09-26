"""HGP detection and in-place patching.

HGP = homegrown player (England secondary nation qual record).
Marker: b10=0x08, b11=0x46, n=0x8b (England, nation ID 139).

Patch strategy: in-place only — no byte insertion, no file size change.
  1. If a b11=0x46 record exists with non-England n: rewrite first 4 bytes to England.
  2. If a b11=0x40 non-HGP override flag exists: flip b11 to 0x47.
"""

ENGLAND_NATION_ID = 0x8b  # 139


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
    """Patch person in bytearray b to be homegrown. Return True if changed."""
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
