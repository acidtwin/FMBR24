"""App settings: one JSON file in the config dir. No Qt imports.

File: <config_dir>/settings.json (shared with fm_editor/weights.py, which owns the
'role_weights_preset' key). Unknown keys are preserved on save. Override the dir with
the FMBR24_CONFIG_DIR env var (tests / verification must never touch the real one).
"""
import json
import os

APP_NAME = 'FM Backroom 24 (FMBR24)'
APP_VERSION = '0.0.0-dev'
APP_REPO_URL = 'https://github.com/acidtwin/FMBR24'
LEGAL_LINE = ('Unofficial tool for Football Manager 24 — not affiliated with or '
              'endorsed by Sports Interactive / SEGA. Football Manager is a trademark '
              'of its owners.')

LANDING_PAGES = ('save_info', 'club', 'players')
ABILITY_DISPLAYS = ('stars', 'numbers')
PLAYER_THEMES = ('steel', 'pitch', 'floodlit', 'plain')  # = ids of gui/pw_themes.THEMES (tests/test_themes.py checks)

DEFAULTS = {
    'default_save_dir': '',            # '' = not set -> old behaviour (Steam dir / home)
    'role_weights_preset': 'FMScout Community',
    'landing_page': 'save_info',       # page opened after a save finishes loading
    'show_pending': True,              # show PENDING chips on the Club page
    'use_cache': True,                 # reuse the parse cache on Load (Reload always re-parses)
    'ability_display': 'stars',        # CA/PA shown as 'stars' or raw 'numbers'
    'player_theme': 'steel',           # player window texture (gui/pw_themes.py registry id)
    'faces_enabled': True,             # show facepack pictures (player window header, staff dialog)
    'logos_enabled': True,             # show club badges from the installed logo packs (same FM24 folder / pack order as faces)
    'flags_enabled': True,             # show nation pictures (lists) and competition logos (Club page) from the logo packs
    'faces_dir': '',                   # FM24 user folder (holds games + graphics); '' = auto-detect (fm_editor/faces.py)
    'faces_pack_order': [],            # facepack folder names, highest priority first (no UI; rest alphabetical)
    'trait_threshold': 11,             # Trait recommender: min average attribute (sheet default, 1-20)
}


def config_dir():
    env = os.environ.get('FMBR24_CONFIG_DIR')
    if env:
        return env
    base = os.environ.get('XDG_CONFIG_HOME') or os.path.join(os.path.expanduser('~'), '.config')
    return os.path.join(base, 'fm24_editor')  # same dir as the old settings dialog / weights


def settings_path():
    return os.path.join(config_dir(), 'settings.json')


def _read_raw():
    try:
        with open(settings_path(), encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _clean(raw):
    """Defaults overlaid with raw, dropping values of the wrong type / out of range."""
    out = dict(DEFAULTS)
    for k, default in DEFAULTS.items():
        v = raw.get(k, default)
        if isinstance(v, type(default)):
            out[k] = v
    if isinstance(out['trait_threshold'], bool) or not 1 <= out['trait_threshold'] <= 20:
        out['trait_threshold'] = DEFAULTS['trait_threshold']
    if out['landing_page'] not in LANDING_PAGES:
        out['landing_page'] = DEFAULTS['landing_page']
    if out['ability_display'] not in ABILITY_DISPLAYS:
        out['ability_display'] = DEFAULTS['ability_display']
    out['faces_pack_order'] = list(out['faces_pack_order'])
    if not all(isinstance(n, str) for n in out['faces_pack_order']):
        out['faces_pack_order'] = list(DEFAULTS['faces_pack_order'])
    if out['player_theme'] not in PLAYER_THEMES:
        out['player_theme'] = DEFAULTS['player_theme']
    return out


def load():
    """Current settings dict (only known keys). Missing/corrupt file -> defaults. Never raises."""
    return _clean(_read_raw())


def save(values):
    """Merge values into the file (unknown keys kept). Returns True on success."""
    try:
        data = _read_raw()
        clean = _clean({**data, **values})
        data.update({k: clean[k] for k in values if k in clean})
        os.makedirs(config_dir(), exist_ok=True)
        tmp = settings_path() + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, settings_path())
        return True
    except Exception:
        return False


def folder_status(path):
    """(state, n_saves): state 'unset' | 'ok' | 'missing' | 'notdir'. n_saves = *.fm files."""
    path = (path or '').strip()
    if not path:
        return 'unset', 0
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        return 'missing', 0
    if not os.path.isdir(path):
        return 'notdir', 0
    try:
        n = sum(1 for e in os.scandir(path) if e.is_file() and e.name.lower().endswith('.fm'))
    except OSError:
        n = 0
    return 'ok', n


def save_dialog_dir(fallback):
    """Start dir for the Load dialog: the configured folder if it is a valid dir, else fallback."""
    p = os.path.expanduser(load()['default_save_dir'].strip())
    return p if p and os.path.isdir(p) else fallback


def ability_as_stars():
    """True when CA/PA should be shown as stars (setting 'ability_display' == 'stars')."""
    return load()['ability_display'] == 'stars'
