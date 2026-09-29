# FM24 Homegrown Editor — Handover

**Last updated:** 2026-09-29 (session 7)
**Project:** `/run/media/acidtwin/Gaming SSD 1/Claude Code Projects/FM-Save-Editor`

---

## Current state

Working FM24 save editor with full FM24-skin UI. Tested against a real Tottenham 2026-27 save.

All changes on `master`. Uncommitted: staff table column auto-sizing, nation flags, shortlist staff support, status bar staff count.

### Session 7 (2026-09-29) — Coaching attrs binary reverse engineering (IN PROGRESS)

**Goal**: Add coaching attribute columns to club staff table.

**Coaching block binary structure** (per-person, after linked records):
- Located by scanning for magic suffix `\x1a\xea\x07` near `records_end + 10`
- First byte of magic varies per save (e.g. `0x60` or `0xc2`) — search for suffix only
- Person ID verified at magic+12 (LE u32, low 16 bits)
- **Section B** (magic+81..+94, 14 bytes) = coaching attrs, divide by 5, clamp 1-20:
  - [0]=WwY(14) [1]=Motivating(12) [2]=?(15) [3]=Determination(17) [4]=Tech(13) [5]=?(15)
  - [6]=Fitness(5) [7]=Attacking(10) [8]=?(12) [9]=?(2) [10]=PeopleM(13) [11]=TactKnowledge(15)
  - [12]=Negotiating(8) [13]=GKHandling(1)
- **Still unknown**: Defending=18 (raw=90), Tactical=16 (raw=80), Level of Discipline=16, JPA=11, JSA=11
- Need binary dumps of 2+ more coaches to find remaining attrs

**Confirmed FM values** (Daniele Baldini id=355, 2026-27 Spurs save):
`Attacking=10 Defending=18 Fitness=5 Mental=15 SetPieces=15 Tactical=16 Technical=13 WwY=14`
`Adaptability=15 Determination=17 LevelOfDiscipline=16 Motivating=12 PeopleManagement=13`
`JPA=11 JPP=10 JSA=11 Negotiating=8 TacticalKnowledge=15 GKHandling=1 GKShotStopping=1`

**Script**: `scripts/probe_staff_attrs.py` — run with name filter to dump coaching block

**Next steps**:
1. Run probe on 2+ more coaches to find Defending/Tactical/etc positions
2. Implement `parse_coaching_block()` in `fm_editor/gamedb.py`
3. Add coaching columns to club staff table
4. User will provide scout/other staff type screenshots after coaching done

### Session 6 (2026-09-29) — Club staff array discovery

**Problem solved**: Find current club for ALL coaching staff (physios, coaches, scouts, analysts). Previous approach (employment records) only found managers + ex-player coaches. Now using club-side staff arrays.

**`find_club_staff(b, clubs, people, abilities, names_start)`** — new function in `fm_editor/gamedb.py`:
- Scans each club's binary record for flat u32 PID arrays (coaching staff lists)
- Pattern: byte immediately before the count byte == `0x00`
- First-PID quick reject: if first u32 in array not in non_ca_ids, skip immediately
- Adjacent array detection: backs up 4 bytes after each valid array (high byte of last PID = 0x00, which is also the marker for the next adjacent array)
- Bounded by next club's offset from sorted club list — correct for all 44,035 clubs
- Uses `bytearray.find(b'\x00')` instead of byte-by-byte loop (~14s vs ~60s)
- Returns `{club_id: [person_ids]}`

**Results for major clubs** (2026-27 save):
- Tottenham Hotspur: 76 staff (coaches, analysts, scouts, physios)
- Liverpool: 75 staff
- Man Utd: 68 staff
- Real Madrid: 60 staff
- Man City: 64 staff

**Key discoveries during investigation**:
- Club id=2 in game_db.dat is an ALBANIAN club (Besëlidhja Lezhë), NOT Arsenal — club IDs are not fixed to English clubs
- There are 44,035 clubs total; average record size ~2200 bytes
- Big English clubs have ~7000-10000 byte records (Liverpool=8284, Man City=7961, Spurs=8296)
- Staff arrays are adjacent (end-to-end), hence the arr_end-4 backup after success
- False-positive filter: non_ca_ids = all_person_ids - player_ids (uses find_abilities result)
- The `b11=0x48` employment record is HGC (Homegrown at Club) training record, NOT staff employment

**Integration**:
- `ParseWorker` calls `find_club_staff` after `find_abilities`; result stored in `_save_data['club_staff']`
- `_populate_staff_table` (global Staff tab): builds `staff_club: {pid: club_id}` reverse map, falls back to `employment` dict for unmatched staff
- `_populate_club_staff_table` (Club Staff tab): uses `club_staff[club_id]` as primary, merges `employment` records
- `cache.py` v10: stores/restores `{club_id: [pids]}` dict

**Removed** from loading: diagnostic sub_squad kind scan (was dead code printing to console).

**Files changed**: `fm_editor/gamedb.py`, `fm_editor/cache.py`, `gui/main_window.py`

---

### Session 5 (2026-09-28) — Role weight presets

**Problem fixed**: Best by Role report surfaced defenders for forward roles (equal-weight scoring of key attrs meant high mental attrs gave defenders comparable scores to strikers).

**Role weight presets system** — `fm_editor/weights.py` + `fm_editor/weights/*.json`:
- **4 bundled presets**: Equal Weight (original behavior), FMScout Community (tiered weights, primary attrs score 20), Possession-Based (boosts passing/vision/technique/composure, softens pace/strength), Direct Play (boosts pace/strength/heading/crossing, softens technical attrs)
- Settings dialog (⚙ button, now wired up): preset dropdown + description. Import custom preset from JSON. Delete user presets.
- **Weight editor dialog**: pick a role → edit per-attribute weights (0-20 spinboxes) → "Save as New Preset" writes to `~/.config/fm24_editor/weights/`
- Active preset persisted in `~/.config/fm24_editor/settings.json`
- `role_rating(person, role_name, weights=None)` — weights param optional, falls back to equal-weight when None
- `_active_preset` loaded at startup in `MainWindow`; re-loaded when settings applied
- Preset name shown in `[FMScout Community]` label next to role dropdown
- Changing preset while Best by Role is open auto-refreshes the report

**Weight generation**: `scripts/gen_weights.py` (scratchpad) — GROUP_PRIMARY + ROLE_PRIMARY_OVERRIDE maps key attr indices to tiered weights; possession/direct play apply ±4 modifiers to technical/physical attr sets.

**New files**: `fm_editor/weights.py`, `fm_editor/weights/equal_weight.json`, `fm_editor/weights/fmscout_community.json`, `fm_editor/weights/possession_based.json`, `fm_editor/weights/direct_play.json`

**Changed files**: `gui/main_window.py` (SettingsDialog, WeightEditorDialog classes; _open_settings, _active_preset, weights label, _get_report_players update), `gui/roles.py` (role_rating weights param)

### Session 4 fixes/features (2026-09-28) — continued

**Status bar black corner fixed**:
- `QSizeGrip` inside `QStatusBar` didn't paint background when launched via desktop shortcut (no terminal). Fixed with `setSizeGripEnabled(False)` — window manager handles resizing.

**Badge text → pure white**:
- All `_POS_BADGE_COLORS` fg values changed to `#FFFFFF` for legibility on all badge backgrounds.

**Dot animation**:
- Changed from ping-pong `[1,2,3,4,5,4,3,2]` to growing cycle `[1,2,3,4]` (`.` `..` `...` `....` repeat).

**Inline search dropdown**:
- Multiple club matches no longer open `QInputDialog`. Instead `_show_search_dropdown()` shows a floating `QFrame(Qt.Popup)` below the search box with clickable club name buttons. Auto-dismisses on outside click.

### Session 4 fixes/features (2026-09-28)

**Sub-squad tabs** — squad view now shows First Team + youth/reserve tabs:
- Two detection strategies combined:
  - **Kind-based** (English clubs): `find_squads` now also captures kinds 18-23 into `sub_squads = {club_id: {kind: [pids]}}`. Kind 100 = first team; 21=U21, 23=U23, 20=Reserves, 19=U19, 18=U18.
  - **Prefix-based** (German/Spanish B teams): clubs named `"Main Club X"` (e.g. "FC Bayern München II") detected by name prefix match, kind 100 squad used.
- `_build_squad_tabs(club, squad)` called from `_show_squad` — removes old dynamic tabs, detects sub-squads, inserts clickable tab buttons before the stretch.
- `_switch_sub_squad(tab_idx, sub_squad)` — updates checked state across all tab buttons, swaps `self._squad`, repopulates table.
- Cache version bumped to 7 (adds `sub_squads` field).

**"First Team" text clipping fixed**:
- Tab bar height 36→40, margins `(12,3,12,0)`, QSS padding `6px→0px` with `min-width:80px`.
- `ft_btn` uses `setSizePolicy(Minimum, Expanding)` instead of `setFixedHeight` — lets Qt compute correct minimum width.

**PyQt6 disconnect() TypeError fixed**:
- `signal.disconnect()` raises `TypeError` (not `RuntimeError`) in PyQt6 6.11 when no connections — all disconnect guards now catch `(RuntimeError, TypeError)`.

**Search crash fixed**:
- `_do_search` wraps `_do_search_inner` in try/except; exceptions show status message instead of crashing to desktop.

**Nav button locking**:
- Squad, Staff, My Shortlist buttons disabled until a save is loaded.

**Column auto-fit**:
- `resizeColumnToContents(i)` called once after populate on all four tables (squad, staff, reports, players).

### Session 3 fixes (2026-09-28)

**Reports CTD — fixed** (commit `fded9c2`):
- Root cause: `clicked(bool)` in PyQt6 6.11 passes checked state as positional arg, overriding lambda default `lambda k=key:` → `_run_report(True)` → `TypeError` → `qFatal()` → crash
- Fix: all sidebar lambdas changed to `lambda checked, k=key:` and `_nav_to_squad_view(self, checked=False)`

**Crash logging — fixed** (commit `338e1dc`):
- `Terminal=false` in desktop shortcut killed all stderr; added `sys.stderr` + `faulthandler` redirect to `/tmp/fm_editor_crash.log` in `main.py`

**Report switching freeze — fixed (this session, uncommitted)**:
- Root cause: `QHeaderView.ResizeMode.ResizeToContents` on cols 1-6 triggered O(n²) text measurement on every `setItem()` across 200 rows × 6 cols
- Fix: switched cols 1-6 to `Interactive` with preset fixed widths (Pos=55, CA/PA/Dev=45, Age=40, Nation=50)
- Also added `QApplication.processEvents()` after button setChecked calls so buttons repaint before populate (eliminates double-glow during any remaining latency)

---

## What the app does

1. **Load** — file-picker for any `.fm` save; parses binary archive (~30–60 s first run, instant from cache)
2. **Search** — type a club name in the topbar search to load their squad, or a player name to find them
3. **Squad view** — shows club squad with Pos (colored badge), CA, PA, Dev Rate, Age, Nation (flag emoji), HGP, HGC columns
4. **Player detail** — double-click a player to open their profile modal (attributes, CA/PA bars, HGP/HGC pills, Make HGP / Make HGC actions)
5. **Patch** — select players in squad view, hit Make HGP or Make HGC; saves to a new file via file dialog (default: `SaveName-Edited-DATE.fm`)
6. **Save Changes** — topbar button writes current binary state to file (no patching)
7. **Reports** — Scouting → Reports sidebar section; table view with Best Prospects (PA≥160), Wonderkids (age≤21, PA≥150), Best in Position (position picker), Best by Role (coming soon)
8. **Players** — Scouting → Players sidebar section; shows all parsed players sorted by CA with name/pos/nation/min-CA/nation filters; player search results land here
9. **Staff** — Staff sidebar entry; 54k+ non-player people showing Name, **Club**, Nation, Age; Club column populated via club-side staff arrays + employment fallback
10. **Club Staff** — Staff tab when viewing a specific club; shows that club's full staff roster (coaches, physios, scouts, analysts)

---

## UI layout (`gui/main_window.py`)

### Stack views (QStackedWidget `_main_stack`)

| Index | Key | View |
|-------|-----|------|
| 0 | `club` | Club overview (name, player/HGP/HGC counts) |
| 1 | `squad` | Squad table (QTableWidget `_table`) |
| 2 | `staff` | Staff table (QTableWidget `_staff_table`) — Name, Club, Nation, Age |
| 3 | `shortlist` | My Shortlist (stub) |
| 4 | `reports` | Scouting Reports table |
| 5 | `players` | All Players view (QTableWidget `_players_table`) |
| 6 | `club_staff` | Club-specific staff table — Name, Nation, Age |

### Topbar

Left: ◀ ▶ breadcrumb | Center: search box (leads to club squad or Players view) | Right: Save Changes · Load · Reload · ⚙

### Sidebar

- **MAIN**: Club, Squad, Staff, My Shortlist
- **SCOUTING**: Players, then Reports sub-section (Best Prospects, Wonderkids, Best in Position, Best by Role)

### Squad table columns

Name | Pos (badge) | CA | PA | Dev | Age | Nation (flag) | HGP | HGC

- Pos column uses `_PosBadgeDelegate` — colored rounded badge (GK=amber, DEF=blue, MID=green, FWD=red)
- Nation column shows flag emoji from `_NATION_FLAG` dict; falls back to nation name

### Players view filters

Name text | Position dropdown | Min CA | Nation dropdown | Clear button

Double-click a player in Players view → navigates to their club's squad.

---

## Key classes / functions

| Symbol | Location | Purpose |
|--------|----------|---------|
| `find_club_staff` | fm_editor/gamedb.py | Scans club binary records for staff PID arrays; returns `{club_id: [pids]}` |
| `find_employment` | fm_editor/gamedb.py | Employment records for managers + ex-player coaches |
| `_populate_staff_table` | main_window.py | Global staff table — Club column via club_staff reverse map |
| `_populate_club_staff_table` | main_window.py | Per-club staff: club_staff primary + employment merge |
| `ParseWorker` | main_window.py | QThread — parses .fm archive |
| `PatchWorker` | main_window.py | QThread — patches HGP/HGC or `mode='save_only'` |
| `PlayerDetailDialog` | main_window.py | Player profile modal (attrs, CA/PA bars, action strip) |
| `_PosBadgeDelegate` | main_window.py | Custom QStyledItemDelegate for Pos column badges |
| `_attr_val_color(v)` | main_window.py | Returns color for attr value (gold ≥17, green ≥16, …) |
| `_NATION_FLAG` | main_window.py | nation_id → flag emoji mapping |
| `_POS_BADGE_COLORS` | main_window.py | pos string → (bg, fg) for badge delegate |
| `NATIONS` | main_window.py | nation_id → nation name (35 entries) |
| `POSITIONS` | main_window.py | FM24 position strings list |
| `find_club_entity_id` | fm_editor/patch.py | Finds club entity ID from b11=0x6a records |
| `is_hgc` | fm_editor/patch.py | Checks HGC status from training records |
| `patch_to_hgc` | fm_editor/patch.py | Patches/inserts HGC training record |

---

## Known limitations / UI stubs

| Feature | Status |
|---------|--------|
| Staff view | Live — Name/Club/Nation(flag)/Age + personality attrs; columns auto-sized; no filters yet |
| Club Staff view | Live — full roster from club-side arrays + employment; ~60-76 per big club; nation flags, auto-sized cols |
| Staff coaching attrs | IN PROGRESS — binary block partially mapped; Defending/Tactical/etc positions still unknown |
| Staff load time | ~14s extra on first load (44k club scan), cached after |
| My Shortlist | Live — Add to Shortlist works from both player and staff modals; shows Name/Club/Type/Pos/CA/PA/Age/Nation |
| Best by Role report | Live — 4 bundled weight presets (FMScout Community default). Weight editor + import in Settings (⚙). |
| ▶ / ▼ navigation buttons | Disabled (greyed) — no back/forward history yet |
| Right tab nav in player modal | Only Profile tab active; Transfer/Positions/Ratings are future |
| Squad number (#) column | Not implemented — mockup had it, excluded by design |
| Sub-squads (U21/B team) | Live — tabs generated from kind-based (English) and prefix-based (German/Spanish) detection. English clubs with no kind-18/21 records in squads won't show sub-tabs. |
| Players view: load all | Currently loads all people with CA data (no explicit limit enforced in filter; display caps at 3000 rows); slow on first open for large saves |
| HGP/HGC patching from cache | Disabled — requires binary `b` in memory; user must Load (not use cached version) |
| Player photo | Placeholder person icon; FM save doesn't store player photos |
| Staff panel (like player panel) | Future — double-click staff member to see role/attribute panel |

---

## Binary format quick-ref

See memory file: `~/.claude/projects/-run-media-acidtwin-Gaming-SSD-1-Claude-Code-Projects-FM-Save-Editor/memory/fm24-binary-format.md`

- **Ability block**: scanned from `names_end + 57`, gate at `b[at-37]==0 && b[at-35]==0`; CA at `b[at-38]`, attrs at `b[at..at+54]`
- **HGP**: secondary nation record `b10=0x08, b11=0x46`
- **HGC**: training record `b10=0x01, b11=0x48`, bytes 0-3 = club entity ID (LE u32); NOT an employment record
- **Personality**: `b[end+17..end+25]` in person record, 8 bytes valid 0-20
- **Club staff array**: flat u32 array within club's binary record; byte before count == `0x00`; multiple adjacent arrays per club (use arr_end-4 backup); bounded by next club's offset in sorted order
- **Employment (non-staff-array)**: `b10=0x01, b11=0x6a` = current employer; `b10=0x01, b11=0x03, b8=0x04` = manager appointment
- **Entity ID**: `club_id + 1` in FM24 (e.g. Spurs club_id=492, entity_id=493)
