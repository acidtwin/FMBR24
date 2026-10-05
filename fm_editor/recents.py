"""Recently viewed players: the last 8 players the user looked at (player window opened, picked on the Compare page, picked in search), newest first, no duplicates. No Qt imports.

Persisted PER SAVE in recent_players.json in the config dir ({save_path: [ids]}); NOT in settings.json, so Reset to defaults and
settings.load() never see it. Ids that are no longer in the save are dropped by the reader (`people_by_id`)."""
import json
import numbers
import os

from fm_editor import settings as _settings

MAX_RECENT = 8


def _path():
    return os.path.join(_settings.config_dir(), 'recent_players.json')


class RecentPlayers:
    def __init__(self, save_path=None, persist=True):
        self._persist = persist
        self._key = save_path or ''
        self._ids = []
        self.load()

    def load(self):
        self._ids = []
        if not self._persist:
            return
        try:
            with open(_path(), encoding='utf-8') as f:
                raw = json.load(f).get(self._key, [])
            self._ids = [i for i in raw if isinstance(i, int)][:MAX_RECENT]
        except (OSError, ValueError, AttributeError):
            pass

    def set_save(self, save_path):
        """Another save was loaded: its own list."""
        self._key = save_path or ''
        self.load()

    def push(self, pid):
        """Move `pid` to the front (LRU of MAX_RECENT) and persist."""
        if not isinstance(pid, numbers.Integral) or isinstance(pid, bool) or pid < 0:   # numpy ints count
            return
        pid = int(pid)
        self._ids = [pid] + [i for i in self._ids if i != pid][:MAX_RECENT - 1]
        self._write()

    def ids(self, exclude=None):
        """Newest first, without `exclude` (the current player)."""
        return [i for i in self._ids if i != exclude]

    def people(self, people_by_id, exclude=None):
        """Person dicts of ids() that still exist in the save."""
        return [people_by_id[i] for i in self.ids(exclude) if i in people_by_id]

    def _write(self):
        if not self._persist:
            return
        try:
            try:
                with open(_path(), encoding='utf-8') as f:
                    data = json.load(f)
                if not isinstance(data, dict):
                    data = {}
            except (OSError, ValueError):
                data = {}
            data[self._key] = self._ids
            os.makedirs(_settings.config_dir(), exist_ok=True)
            tmp = _path() + '.tmp'
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(data, f)
            os.replace(tmp, _path())
        except OSError:
            pass
