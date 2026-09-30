"""Current-season player stats from ``rgman/player_stats.dat`` (see memory fm24-binary-format.md s.7).

The member is a run of per-person records ``01 <u32 person id> ...`` sorted by id.  Every player
has one; ~16k (clubs whose leagues are simulated in detail) carry stat blocks.  A stat block is
``01 06`` + 137 bytes; fields (LE, offsets from the ``01``):

  +2 u16 rating sum (per-match ratings x10, summed)   +4 u16 minutes
  +6 u8 starts  +7 u8 sub apps  +8 u8 rated apps (apps that count towards the average)
  +9 u8 goals   +10 u8 assists  +14 u8 player of the match  (+16 u8 yellow cards: plausible only)

Blocks are per competition group (friendlies, league, cups, continental, youth/other ...), in a
variable-length list that also holds the OVERALL block (what the in-game Squad screen shows) and
a couple of "last match" blocks; there is no type tag, so the overall block is located by value:
it equals the field-wise sum of a subset of the blocks before it.
"""
import bisect
import itertools
import re
import struct

_MIN_BLOCK = 139     # 01 06 + fixed fields; real blocks are 139-142 bytes apart
_MAX_REC = 4096      # longest real record seen: 1,789 bytes
_MAX_SUBSET = 4      # overall = sum of at most this many earlier blocks
_MARK = re.compile(rb'(?=\x01...\x00)', re.S)


def find_records(data, ids):
    """{person id: record bytes} (ids must cover every person, see parse_player_stats). Candidates `01 <id>` are filtered by id set, then the longest
    id-increasing chain is kept (records are sorted; stray hits inside a record's data break the
    order and are dropped)."""
    idset = set(ids)
    cand = []
    for m in _MARK.finditer(data):
        o = m.start()
        pid = data[o + 1] | data[o + 2] << 8 | data[o + 3] << 16
        if pid in idset:
            cand.append((o, pid))
    tails, tail_idx, prev = [], [], [-1] * len(cand)
    for k, (_, pid) in enumerate(cand):
        p = bisect.bisect_left(tails, pid)
        if p == len(tails):
            tails.append(pid); tail_idx.append(k)
        else:
            tails[p] = pid; tail_idx[p] = k
        prev[k] = tail_idx[p - 1] if p else -1
    seq = []
    k = tail_idx[-1] if tail_idx else -1
    while k != -1:
        seq.append(cand[k]); k = prev[k]
    seq.reverse()
    # cap: records are <= ~1.8 KB; an id missing from `ids` must not swallow its successors
    return {pid: data[o:min(seq[i + 1][0] if i + 1 < len(seq) else len(data), o + _MAX_REC)]
            for i, (o, pid) in enumerate(seq)}


def _blocks(rec):
    """List of (rating_sum, minutes, starts, subs, rated, goals, assists, pom) per stat block."""
    starts = []
    p = rec.find(b'\x01\x06')
    while p >= 0:
        if not starts or p - starts[-1] >= 130:   # `01 06` also occurs inside field data
            starts.append(p)
        p = rec.find(b'\x01\x06', p + 1)
    out = []
    for o in starts:
        if o + _MIN_BLOCK > len(rec):
            break
        rs, mins = struct.unpack_from('<HH', rec, o + 2)
        out.append((rs, mins, rec[o + 6], rec[o + 7], rec[o + 8], rec[o + 9], rec[o + 10],
                    rec[o + 14]))
    return out


def overall_block(blocks):
    """The overall (all competitive) block: the block with the most appearances (>= 2) that equals
    the field-wise sum of 1..4 earlier blocks; later block wins ties. None if there is none (a player
    with fewer than 2 competitive appearances has no reliable figure). Compared fields: rating sum,
    minutes, starts, subs, rated, goals, assists."""
    best = None
    for j in range(1, len(blocks)):
        b = blocks[j]
        apps = b[2] + b[3]
        if apps < 2 or (best is not None and apps < best[0]):
            continue
        for k in range(1, min(_MAX_SUBSET, j) + 1):
            if any(all(sum(blocks[x][f] for x in sub) == b[f] for f in range(7))
                   for sub in itertools.combinations(range(j), k)):
                best = (apps, j)
                break
    return blocks[best[1]] if best else None


def parse_player_stats(data, person_ids):
    """{player id: stats dict} for players with an identifiable overall block.

    person_ids must cover EVERY person in the save (players and staff): a record runs up to the
    next known id, so an id left out would make the previous record swallow its successor.

    Keys: starts, subs, apps (starts+subs), goals, assists, mins, pom, rated (apps that count
    towards the rating), rating (average match rating, e.g. 7.05, None if nothing rated)."""
    out = {}
    for pid, rec in find_records(data, person_ids).items():
        if len(rec) < 240:
            continue
        ob = overall_block(_blocks(rec))
        if ob is None:
            continue
        rs, mins, st, sub, rated, g, ast, pom = ob
        out[pid] = {'starts': st, 'subs': sub, 'apps': st + sub, 'goals': g, 'assists': ast,
                    'mins': mins, 'pom': pom, 'rated': rated,
                    'rating': rating(rs, rated)}
    return out


def rating(rating_sum, rated):
    """Average match rating: rating sum (x10) / rated apps, two decimals; None if nothing rated."""
    return round(rating_sum / rated / 10, 2) if rated else None
