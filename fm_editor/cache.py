"""JSON cache for parsed save data, keyed by file mtime.

Cache file: ~/.cache/fm24_editor/<sha256_of_path>.json
Stores: mtime, clubs list, squads dict, sub_squads dict, people list.
Re-parse if mtime changed or cache missing.
"""
import json
import os
import hashlib


_CACHE_DIR = os.path.join(os.path.expanduser('~'), '.cache', 'fm24_editor')


def _cache_path(save_path):
    key = hashlib.sha256(save_path.encode()).hexdigest()[:16]
    return os.path.join(_CACHE_DIR, f"{key}.json")


_CACHE_VERSION = 14  # bump when schema changes to auto-invalidate old caches


def load_cache(save_path):
    """Return cached dict if valid for current mtime, else None."""
    cp = _cache_path(save_path)
    if not os.path.exists(cp):
        return None
    try:
        with open(cp, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if data.get('version', 1) != _CACHE_VERSION:
            return None
        mtime = os.path.getmtime(save_path)
        if abs(data.get('mtime', 0) - mtime) > 1:
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


def save_cache(save_path, clubs, squads, sub_squads, people, employment=None, club_staff=None):
    os.makedirs(_CACHE_DIR, exist_ok=True)
    cp = _cache_path(save_path)
    slim_people = []
    for p in people:
        if p.get('id', -1) == -1:
            continue
        entry = {'id': p['id'], 'name': p['name'], 'nation': p['nation'],
                 'birth_year': p['birth_year'], 'end': p['end'], 'offset': p['offset'],
                 'hgp': p.get('hgp', False), 'personality': p.get('personality', [])}
        if 'ca' in p:
            entry['ca'] = p['ca']
            entry['pa'] = p['pa']
            entry['positions'] = p['positions']
            entry['raw_attrs'] = p['raw_attrs']
            entry['injured'] = p.get('injured', False)
            entry['injury_days'] = p.get('injury_days', 0)
        else:
            # Non-player staff fields
            if 'coaching' in p:
                entry['coaching'] = p['coaching']
            if 'staff_ca' in p:
                entry['staff_ca'] = p['staff_ca']
                entry['staff_pa'] = p['staff_pa']
        if 'contract_end' in p:
            entry['contract_end'] = p['contract_end']
        slim_people.append(entry)
    data = {
        'version': _CACHE_VERSION,
        'mtime': os.path.getmtime(save_path),
        'clubs': clubs,
        'squads': squads,
        'sub_squads': sub_squads,
        'people': slim_people,
    }
    if employment:
        data['employment'] = employment
    if club_staff:
        data['club_staff'] = club_staff
    try:
        with open(cp, 'w', encoding='utf-8') as f:
            json.dump(data, f, separators=(',', ':'))
    except Exception:
        pass  # cache write failure is non-fatal
