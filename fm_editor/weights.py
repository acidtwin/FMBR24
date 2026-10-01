"""Role attribute weight presets for Best by Role scoring.

Bundled presets live in fm_editor/weights/*.json.
User presets live in ~/.config/fm24_editor/weights/*.json.

Preset JSON format:
  {
    "name": "...",
    "description": "...",
    "tactical_style": "...",   # optional
    "roles": {
      "Advanced Forward (A)": {"2": 20, "6": 18, ...},
      ...
    }
  }
  Empty "roles" dict = equal weight fallback (no weights applied).
"""
import json
import shutil
from pathlib import Path

from fm_editor import settings as _app_settings

_BUNDLED_DIR = Path(__file__).parent / 'weights'


def _user_dir() -> Path:
    return Path(_app_settings.config_dir()) / 'weights'


_ACTIVE_KEY = 'role_weights_preset'
_DEFAULT_PRESET = 'FMScout Community'


def list_presets() -> list[dict]:
    """Return list of preset info dicts, bundled first then user, sorted by name."""
    presets = []
    for bundled, d in ((True, _BUNDLED_DIR), (False, _user_dir())):
        if not d.exists():
            continue
        for f in sorted(d.glob('*.json')):
            try:
                with open(f, encoding='utf-8') as fh:
                    data = json.load(fh)
                presets.append({
                    'name': data.get('name', f.stem),
                    'description': data.get('description', ''),
                    'tactical_style': data.get('tactical_style', ''),
                    'path': str(f),
                    'bundled': bundled,
                })
            except Exception:
                pass
    return presets


def load_preset(path: str) -> dict:
    """Load preset from path. Normalises role weight keys to int."""
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    roles = {}
    for role_name, attrs in data.get('roles', {}).items():
        roles[role_name] = {int(k): int(v) for k, v in attrs.items()}
    data['roles'] = roles
    return data


def get_active_preset_name() -> str:
    try:
        with open(_app_settings.settings_path(), encoding='utf-8') as f:
            return json.load(f).get(_ACTIVE_KEY, _DEFAULT_PRESET)
    except Exception:
        return _DEFAULT_PRESET


def set_active_preset_name(name: str):
    """Atomic merge into settings.json (via settings.save; unknown keys kept)."""
    _app_settings.save({_ACTIVE_KEY: name})


def load_active_preset() -> dict | None:
    """Load currently active preset. Falls back to first available."""
    name = get_active_preset_name()
    presets = list_presets()
    for p in presets:
        if p['name'] == name:
            try:
                return load_preset(p['path'])
            except Exception:
                break
    if presets:
        try:
            return load_preset(presets[0]['path'])
        except Exception:
            pass
    return None


def get_role_weights(preset: dict | None, role_name: str) -> dict[int, int] | None:
    """Return weight dict {attr_idx: weight} for role_name, or None for equal-weight."""
    if not preset:
        return None
    return preset.get('roles', {}).get(role_name) or None


def import_preset(source_path: str) -> str:
    """Copy a JSON preset file to user weights dir. Returns preset name."""
    _user_dir().mkdir(parents=True, exist_ok=True)
    src = Path(source_path)
    with open(src, encoding='utf-8') as f:
        data = json.load(f)
    name = data.get('name', src.stem)
    dest = _user_dir() / src.name
    shutil.copy2(src, dest)
    return name


def save_custom_preset(name: str, description: str,
                        roles_weights: dict[str, dict[int, int]]) -> str:
    """Write a custom preset to user weights dir. Returns path."""
    _user_dir().mkdir(parents=True, exist_ok=True)
    safe = ''.join(c if c.isalnum() or c in ' -_' else '_' for c in name)
    path = _user_dir() / f"{safe.replace(' ', '_').lower()}.json"
    roles_str = {
        role: {str(k): v for k, v in sorted(w.items())}
        for role, w in roles_weights.items()
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({
            'name': name,
            'description': description,
            'tactical_style': 'Custom',
            'roles': roles_str,
        }, f, indent=2)
    return str(path)


def delete_user_preset(name: str) -> bool:
    """Delete a user preset by name. Returns True if deleted."""
    for p in list_presets():
        if p['name'] == name and not p['bundled']:
            Path(p['path']).unlink(missing_ok=True)
            return True
    return False
