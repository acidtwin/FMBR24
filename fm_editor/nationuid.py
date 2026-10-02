"""Our nation entity id -> the nation's game UniqueID, the key the logo packs file nation pictures under
(`graphics/pictures/nation/<uid>/logo`). Pure python, no Qt.

Our ids (club record +13, person end+9, `fm_editor/nations.py`) are the ordinal of the nation table in the FM24 install
database: `data/database/db/<ver>/<ver>_fm/server_db.dat` (tad wrapper, FMF archive from byte 8), members `table_9.dat` and
`table_10.dat`, whose nation records start `[ordinal u32][uid u32][uid u32]`. Both tables give the same 251 pairs (ordinal
0..250; found by scanning for the triplet and chaining ordinals in file order). The uids are not contiguous (Africa 5-55,
Asia 106-146, CONCACAF 359-390 + 574-584, Europe 752-802 ...), so a plain offset is wrong for CONCACAF and beyond; this table is
the exact mapping. It is static game data (the nations do not change between saves), so it ships as a table instead of reading
the 82 MB install database at run time.
Verified by eye on the FMG Standard Logos nation crests (Europe, Africa, Asia, CONCACAF, South America) and by hit rate in
tests/test_list_media.py (live part).
"""
NATION_UID = (
    5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29,
    30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53,
    54, 55, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122,
    123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141,
    142, 143, 144, 145, 146, 359, 360, 361, 362, 363, 364, 365, 366, 367, 368, 370, 371, 373, 374,
    375, 376, 377, 379, 380, 381, 382, 383, 384, 385, 386, 387, 388, 389, 390, 574, 575, 577, 583,
    584, 752, 753, 754, 755, 756, 757, 758, 759, 760, 761, 762, 763, 764, 765, 766, 767, 768, 769,
    770, 771, 772, 773, 774, 775, 776, 777, 778, 779, 780, 781, 782, 783, 784, 785, 786, 787, 788,
    789, 790, 791, 792, 793, 794, 795, 796, 797, 798, 799, 800, 801, 802, 1435, 1436, 1437, 1438,
    1439, 1440, 1441, 1442, 1443, 1444, 1649, 1650, 1651, 1652, 1653, 1654, 1655, 1656, 1657, 1658,
    1662, 100349, 103277, 114502, 129504, 129505, 129508, 129511, 129514, 129517, 129520, 129523,
    129526, 129532, 131012, 142527, 145174, 208996, 209002, 214394, 214395, 215446, 217945, 219003,
    788980, 788987, 788995, 788999, 917496, 917498, 917502, 917506, 917508, 917510, 918740, 918745,
    918748, 919586, 5626565, 5626837, 5630219, 8162661, 13100103, 13113220, 13116454, 15064643,
    23008660, 23088616, 29118470, 52024163, 62002127, 62003815, 82082526, 82082540
)


def nation_uid(nation_id):
    """UniqueID of the nation with our entity id, or None for an unknown id."""
    try:
        return NATION_UID[nation_id] if nation_id is not None and nation_id >= 0 else None
    except (IndexError, TypeError):
        return None
