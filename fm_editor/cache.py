"""JSON cache for parsed save data, validated by file mtime_ns + size.

Cache file: ~/.cache/fm24_editor/<sha256_of_path>.json
Stores: mtime_ns, size, clubs list, squads dict, sub_squads dict, people list, save_info dict.
Re-parse if mtime or size changed or cache missing.
"""
import json
import os
import hashlib


_CACHE_DIR = os.path.join(os.path.expanduser('~'), '.cache', 'fm24_editor')


def _cache_path(save_path):
    key = hashlib.sha256(save_path.encode()).hexdigest()[:16]
    return os.path.join(_CACHE_DIR, f"{key}.json")


_CACHE_VERSION = 30  # bump when schema changes to auto-invalidate old caches


def file_signature(save_path):
    """(mtime_ns, size) of the save; capture BEFORE reading it, pass to save_cache."""
    st = os.stat(save_path)
    return st.st_mtime_ns, st.st_size


def load_cache(save_path):
    """Return cached dict if valid for the save's current mtime_ns and size, else None."""
    cp = _cache_path(save_path)
    if not os.path.exists(cp):
        return None
    try:
        with open(cp, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if data.get('version', 1) != _CACHE_VERSION:
            return None
        if [data.get('mtime_ns'), data.get('size')] != list(file_signature(save_path)):
            return None
        # JSON dict keys are always strings; normalize back to int keys
        if 'squads' in data:
            data['squads'] = {int(k): int(v) for k, v in data['squads'].items()}
        if 'sub_squads' in data:
            data['sub_squads'] = {
                int(cid): {int(kind): pids for kind, pids in kinds.items()}
                for cid, kinds in data['sub_squads'].items()
            }
        if 'employment' in data:
            data['employment'] = {int(k): int(v) for k, v in data['employment'].items()}
        if 'club_staff' in data:
            data['club_staff'] = {int(k): v for k, v in data['club_staff'].items()}
        return data
    except Exception:
        return None


def clear_cache(save_path):
    """Delete the cache file for a save, if it exists."""
    try:
        os.remove(_cache_path(save_path))
    except FileNotFoundError:
        pass


def save_cache(save_path, clubs, squads, sub_squads, people, employment=None, club_staff=None,
               save_info=None, sig=None):
    """sig: file_signature() taken before the parse; a save changed since is not cached."""
    sig = sig or file_signature(save_path)
    if sig != file_signature(save_path):
        return
    os.makedirs(_CACHE_DIR, exist_ok=True)
    cp = _cache_path(save_path)
    slim_people = []
    for p in people:
        if p.get('id', -1) == -1:
            continue
        entry = {'id': p['id'], 'name': p['name'], 'nation': p['nation'],
                 'birth_year': p['birth_year'], 'birth_day': p.get('birth_day', 0), 'end': p['end'], 'offset': p['offset'],
                 'hgp': p.get('hgp', False), 'personality': p.get('personality', []),
                 'trait_mask': p.get('trait_mask', 0)}
        if 'ca' in p:
            entry['ca'] = p['ca']
            entry['pa'] = p['pa']
            entry['positions'] = p['positions']
            entry['raw_attrs'] = p['raw_attrs']
            entry['height_cm'] = p.get('height_cm')
            entry['weight_kg'] = p.get('weight_kg')
            entry['value_est'] = p.get('value_est')
            entry['injured'] = p.get('injured', False)
            entry['injury_days'] = p.get('injury_days', 0)
            if 'stats' in p:
                entry['stats'] = p['stats']
        else:
            # Non-player staff fields
            if 'coaching' in p:
                entry['coaching'] = p['coaching']
            if 'staff_ca' in p:
                entry['staff_ca'] = p['staff_ca']
                entry['staff_pa'] = p['staff_pa']
        if 'contract_end' in p:
            entry['contract_end'] = p['contract_end']
        if 'contract_start' in p:
            entry['contract_start'] = p['contract_start']
        if 'wage_week' in p:
            entry['wage_week'] = p['wage_week']
        slim_people.append(entry)
    data = {
        'version': _CACHE_VERSION,
        'mtime_ns': sig[0],
        'size': sig[1],
        'clubs': clubs,
        'squads': squads,
        'sub_squads': sub_squads,
        'people': slim_people,
    }
    if employment:
        data['employment'] = employment
    if club_staff:
        data['club_staff'] = club_staff
    if save_info:
        data['save_info'] = save_info  # plain JSON types (str/int/list) - no key normalising needed
    try:
        with open(cp, 'w', encoding='utf-8') as f:
            json.dump(data, f, separators=(',', ':'))
    except Exception:
        pass  # cache write failure is non-fatal


def cache_dir():
    return _CACHE_DIR


def _cache_files():
    """Cache files: *.json directly inside the cache dir (regular files, no symlinks)."""
    try:
        return [e.path for e in os.scandir(_CACHE_DIR)
                if e.name.endswith('.json') and e.is_file(follow_symlinks=False)]
    except OSError:
        return []


def cache_info():
    """(n_files, total_bytes) of the parse cache."""
    n = size = 0
    for p in _cache_files():
        try:
            size += os.path.getsize(p)
            n += 1
        except OSError:
            pass
    return n, size


def clear_all_caches():
    """Delete every parse-cache file. Only touches *.json inside the cache dir. Returns count."""
    n = 0
    for p in _cache_files():
        if os.path.dirname(os.path.realpath(p)) != os.path.realpath(_CACHE_DIR):
            continue
        try:
            os.remove(p)
            n += 1
        except OSError:
            pass
    return n
