"""Background QThread workers (no widgets touched; results go back through signals)."""
from PyQt6.QtCore import QThread, pyqtSignal
from fm_editor.cache import load_cache, save_cache, file_signature


class ParseWorker(QThread):
    progress = pyqtSignal(str)
    pct = pyqtSignal(int)
    done = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, save_path, use_cache=False):
        super().__init__()
        self.save_path = save_path
        self.use_cache = use_cache

    def _emit(self, msg, p):
        self.progress.emit(msg)
        self.pct.emit(p)

    def _club_extras(self, b, members, clubs, get_member):
        """Reputation, stadium, league position (fm_editor/clubextra.py); best effort per member."""
        import re
        from fm_editor import clubextra as X
        self._emit("Reading club reputation, stadiums and tables...", 58)
        X.add_club_status(b, clubs)
        by_name = {m['name']: m for m in members}
        fm = by_name.get('rgman/fix_man.dat')
        fix = get_member(self.save_path, fm) if fm else None
        if fix:
            X.add_club_stadiums(b, clubs, fix)
        tables = []
        for n, m in by_name.items():
            if re.fullmatch(r'rgman/comp_\d+\.dat', n):
                tables.append(X.parse_comp_table(get_member(self.save_path, m)))
        X.add_league_positions(clubs, tables, fix)

    def _human_clubs(self, b, members, save_info, people, clubs):
        """Human-managed club ids (fm_editor.saveinfo.human_club_ids); cheap, so never cached."""
        try:
            from fm_editor.archive import get_member
            from fm_editor.saveinfo import human_club_ids
            hm = next((m for m in members if m['name'] == 'humans.dat'), None)
            return human_club_ids({'save_info': save_info, 'b': b, 'people': people, 'clubs': clubs},
                                  get_member(self.save_path, hm) if hm else None)
        except Exception:
            import traceback
            traceback.print_exc()
            return {(save_info or {}).get('manager_club_id')} - {None}

    def run(self):
        try:
            from fm_editor.archive import parse_archive, get_member
            from fm_editor.gamedb import (find_names, find_clubs, add_club_finance, find_squads,
                                          find_people, match_identities, find_abilities,
                                          find_employment, find_contracts, find_club_staff,
                                          find_coaching_attrs, find_injuries,
                                          find_staff_extras)
            from fm_editor.patch import is_homegrown

            sig = file_signature(self.save_path)  # before any read: save_cache refuses if it changed
            self._emit("Parsing archive...", 3)
            header, members, index_marker, archive_name, subdir_count, subdirs = \
                parse_archive(self.save_path)
            gdb_m_ref = next((m for m in members if m['name'] == 'game_db.dat'), None)

            if not gdb_m_ref:
                self.error.emit("game_db.dat not found in archive.")
                return

            self._emit(f"Extracting game_db.dat ({gdb_m_ref['p'] // 1024 // 1024} MB)...", 5)
            b = get_member(self.save_path, gdb_m_ref)

            cached = load_cache(self.save_path) if self.use_cache else None
            if cached and all(k in cached for k in ('clubs', 'squads', 'sub_squads', 'people')):
                self.pct.emit(100)  # fast path: parsed data from cache; b/header/members still needed to patch+save
                self.done.emit({
                    'clubs': cached['clubs'], 'squads': cached['squads'],
                    'sub_squads': cached['sub_squads'], 'people': cached['people'],
                    'employment': cached.get('employment', {}), 'club_staff': cached.get('club_staff', {}),
                    'save_info': cached.get('save_info', {}),
                    'club_uids_extra': cached.get('club_uids_extra', []),
                    'human_clubs': self._human_clubs(b, members, cached.get('save_info', {}),
                                                     cached['people'], cached['clubs']),
                    'b': b, 'header': header, 'members': members,
                    'index_marker': index_marker, 'archive_name': archive_name,
                    'subdir_count': subdir_count, 'subdirs': subdirs,
                    'disk_sig': (sig[1], sig[0]),  # savefile.file_signature order: (size, mtime_ns)
                })
                return

            self._emit("Finding name tables...", 45)
            first_names, last_names, names_start, names_end = find_names(b)

            self._emit("Finding clubs...", 55)
            clubs = find_clubs(b, names_start)
            add_club_finance(b, clubs, names_start)
            from fm_editor.gamedb import find_hidden_club_uids
            club_uids_extra = find_hidden_club_uids(b, names_start)
            try:
                self._club_extras(b, members, clubs, get_member)
            except Exception:
                import traceback
                traceback.print_exc()  # reputation/stadium/table are optional: Club page hides the row

            self._emit("Finding people and matching identities...", 65)
            people = find_people(b, first_names, last_names, names_end)
            match_identities(b, people, names_end)

            self._emit("Finding squad memberships...", 72)
            squads, sub_squads = find_squads(b, clubs, names_start, people)

            self._emit("Checking homegrown status...", 82)
            for p in people:
                p['hgp'] = is_homegrown(b, p)

            self._emit("Scanning abilities (CA/PA)...", 88)
            abilities = find_abilities(b, names_end)
            for p in people:
                ab = abilities.get(p.get('id', -1))
                if ab:
                    p['ca'] = ab['ca']
                    p['pa'] = ab['pa']
                    p['positions'] = ab['positions']
                    p['raw_attrs'] = ab['raw_attrs']
                    p['height_cm'] = ab['height_cm']
                    p['weight_kg'] = ab['weight_kg']
                    p['value_est'] = ab.get('value_est')

            self._emit("Scanning employment records...", 91)
            employment = find_employment(b, people)

            self._emit("Scanning contract dates...", 92)
            from fm_editor.gamedb import find_contract_blocks
            contracts = find_contract_blocks(b, people)  # real block (old 0x6a record = last evaluation month)
            for p in people:
                c = contracts.get(p.get('id', -1))
                if c:
                    p.update(c)

            self._emit("Scanning club staff arrays...", 93)
            club_staff = find_club_staff(b, clubs, people, abilities, names_start)

            player_ids = set(abilities.keys())
            self._emit("Parsing coaching attributes...", 94)
            find_coaching_attrs(b, people, player_ids)
            self._emit("Parsing staff ability (CA/PA)...", 96)
            find_staff_extras(b, people, player_ids)

            self._emit("Reading season stats...", 96)
            try:
                from fm_editor.playerstats import parse_player_stats
                ps_m = next((m for m in members if m['name'] == 'rgman/player_stats.dat'), None)
                if ps_m:
                    stats = parse_player_stats(get_member(self.save_path, ps_m),
                                              {p['id'] for p in people if p.get('id', -1) != -1})
                    for p in people:
                        if p.get('id') in stats:
                            p['stats'] = stats[p['id']]
            except Exception:
                import traceback
                traceback.print_exc()  # season stats are optional: the Club page falls back to CA

            self._emit("Reading save info...", 97)
            try:
                from fm_editor.saveinfo import parse_save_info
                save_info = parse_save_info(self.save_path, members, archive_name,
                                            gdb=b, clubs=clubs, people=people)
            except Exception:
                import traceback
                traceback.print_exc()  # untrusted bytes: a bad metadata block must not abort the load
                save_info = {}

            self._emit("Scanning injuries...", 97)
            try:  # injuries live in injury_manager.dat (the game_db 0x47 record is NOT an injury)
                import datetime as _dt
                from fm_editor.gamedb import parse_injury_manager
                im = next((m for m in members if m['name'] == 'injury_manager.dat'), None)
                inj = parse_injury_manager(get_member(self.save_path, im)) if im else None
                today = _dt.date.fromisoformat(str((save_info or {}).get('in_game_date'))[:10])
            except Exception:
                import traceback
                traceback.print_exc()
                inj, today = None, None
            find_injuries(b, people, player_ids, inj, today)

            try:  # scouting budget: only the human-managed club carries it
                from fm_editor.clubextra import find_human_scouting_budget
                sb, hc = find_human_scouting_budget(b), (save_info or {}).get('manager_club_id')
                hc_club = next((c for c in clubs if c['id'] == hc), None) if sb else None
                if hc_club is not None:
                    hc_club.setdefault('fin', {})['scouting_budget'] = sb[0]
            except Exception:
                pass

            human_clubs = self._human_clubs(b, members, save_info, people, clubs)

            self._emit("Caching results...", 98)
            save_cache(self.save_path, clubs, squads, sub_squads, people, employment, club_staff,
                       save_info, sig=sig, club_uids_extra=club_uids_extra)

            self.pct.emit(100)
            result = {
                'clubs': clubs, 'squads': squads, 'sub_squads': sub_squads, 'people': people,
                'employment': employment, 'club_staff': club_staff, 'save_info': save_info,
                'club_uids_extra': club_uids_extra, 'human_clubs': human_clubs,
                'b': b, 'header': header, 'members': members,
                'index_marker': index_marker, 'archive_name': archive_name,
                'subdir_count': subdir_count, 'subdirs': subdirs,
                'disk_sig': (sig[1], sig[0]),  # taken before the first read; Save refuses if the file differs
            }
            self.done.emit(result)

        except Exception as e:
            self.error.emit(str(e))


class SaveWorker(QThread):
    """Save Changes: verified temp file, 2 rotating backups, atomic replace (fm_editor/savefile.py)."""
    progress = pyqtSignal(str)
    pct = pyqtSignal(int)
    done = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, save_data, path):
        super().__init__()
        self.save_data = save_data
        self.path = path

    def run(self):
        try:
            from fm_editor.savefile import save_in_place

            def _cb(msg, p):
                self.progress.emit(msg)
                self.pct.emit(p)

            self.done.emit(save_in_place(self.save_data, self.path, _cb))
        except Exception as e:
            self.error.emit(str(e))
