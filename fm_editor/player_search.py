"""Name search ranking shared by the main search box and the Compare / player-window pickers. No Qt imports.

`index` = MainWindow._sg_index(): [(lowercase name, name, kind, obj)], kind 0 club / 1 staff / 2 player. Rank: name starts with
the query (0), a word starts with it (1), anywhere (2); then kind, then name."""
import heapq

POS_GK = 0   # index of GK in the 15 position ratings (gui.player_window.POS_ORDER); a keeper's best rating is there


def is_keeper(person):
    """Primary position is GK (highest of the 15 position ratings, ties to the first = GK, as main_window._primary_pos)."""
    pos = person.get('positions')
    return bool(pos) and pos.index(max(pos)) == POS_GK


def rank_hits(index, query, limit=12, kinds=None, exclude_ids=(), keeper=None):
    """[(rank, kind, name, obj)] best first, at most `limit`. kinds None = all; exclude_ids = person ids to skip;
    keeper True / False keeps only keepers / outfield players (people only)."""
    q = (query or '').strip().lower()
    if not q:
        return []
    sp = ' ' + q
    hits = []
    for e in index:
        if q not in e[0] or (kinds is not None and e[2] not in kinds):
            continue
        if e[2] != 0 and (e[3].get('id') in exclude_ids or (keeper is not None and is_keeper(e[3]) != keeper)):
            continue
        hits.append(((0 if e[0].startswith(q) else 1 if sp in e[0] else 2), e[2], e[1], e[3]))
    return heapq.nsmallest(limit, hits, key=lambda h: h[:3])
