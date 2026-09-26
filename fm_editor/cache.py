"""JSON cache for parsed save data, keyed by file mtime.

Cache file: ~/.cache/fm24_editor/<sha256_of_path>.json
Stores: mtime, clubs list, squad dict, people list (id/name/nation/birth_year/end).
Re-parse if mtime changed or cache missing.
"""
import json
import os
import hashlib


_CACHE_DIR = os.path.join(os.path.expanduser('~'), '.cache', 'fm24_editor')


def _cache_path(save_path):
    key = hashlib.sha256(save_path.encode()).hexdigest()[:16]
    return os.path.join(_CACHE_DIR, f"{key}.json")


def load_cache(save_path):
    """Return cached dict if valid for current mtime, else None."""
    cp = _cache_path(save_path)
    if not os.path.exists(cp):
        return None
    try:
        with open(cp, 'r', encoding='utf-8') as f:
            data = json.load(f)
        mtime = os.path.getmtime(save_path)
        if abs(data.get('mtime', 0) - mtime) > 1:
            return None
        return data
    except Exception:
        return None


def save_cache(save_path, clubs, squads, people):
    os.makedirs(_CACHE_DIR, exist_ok=True)
    cp = _cache_path(save_path)
    slim_people = [
        {'id': p['id'], 'name': p['name'], 'nation': p['nation'],
         'birth_year': p['birth_year'], 'end': p['end'], 'offset': p['offset']}
        for p in people if p.get('id', -1) != -1
    ]
    data = {
        'mtime': os.path.getmtime(save_path),
        'clubs': clubs,
        'squads': squads,
        'people': slim_people,
    }
    try:
        with open(cp, 'w', encoding='utf-8') as f:
            json.dump(data, f, separators=(',', ':'))
    except Exception:
        pass  # cache write failure is non-fatal
