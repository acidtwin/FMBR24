# FM24 Homegrown Editor — Handover

**Last updated:** 2026-09-30 (session 11)
**Project:** `/run/media/acidtwin/Gaming SSD 1/Claude Code Projects/FM-Save-Editor`

---

## Current state

Working FM24 save editor with full FM24-skin UI. Tested against a real Tottenham 2026-27 save.
All changes on `master`. Cache version: **15**.

---

## Session 11 (2026-09-30) — Filter bar labels, squad tab bar, sidebar texture

### Filter bars renamed to "Quick Filters" (COMPLETE)

- **Players**: title label "Players" → "Quick Filters" (secondary/11px — was bold primary)
- **Scouting Staff**: header label "Staff" → "Quick Filters"
- **Reports**: "Quick Filters" label added at start of `filter_frame` row (below "Scouting Reports" header)
- **Club Staff**: new 38px "Quick Filters" placeholder bar added below "Club Staff" header (no filters yet)
- **Squads tab bar**: unchanged (user approved current state)

### Squad tab bar background (COMPLETE)

- Background changed from `COLORS['surface']` (`#1A2226`, greenish-tinted) → `COLORS['elevated']` (`#292B32`, grey) — matches all other page filter bars
- Make HGP / Make HGC disabled state: was `background:elevated` (invisible on new elevated bar) → `background:surface + border:1px solid border` so disabled buttons stay visible

### Sidebar brushed-metal texture overlay (COMPLETE)

- `_SidebarFrame(QFrame)` subclass — overrides `paintEvent`: calls `PE_Widget` first (respects QSS bg + border), then draws `sidebar.webp` scaled to fill at **0.22 opacity**
- Image: `gui/assets/sidebar.webp` — dark brushed-metal carbon texture (192×900-ish portrait)
- `_make_sidebar` creates `_SidebarFrame()` instead of `QFrame()`, loads image after `vbox.addStretch()`
- Opacity dial: change `p.setOpacity(0.22)` in `_SidebarFrame.paintEvent` to adjust

### Club page mockup saved (COMPLETE)

- `mockups/club-page-design-a.html` — local copy of the Claude artifact (Design A "Stadium Hero")
- Artifact URL: `https://claude.ai/artifact/ShmMMFy65UH5r4NZ4u4RqH`

### Subagent workflow established

- Coding edits now delegated to `caveman:cavecrew-builder` subagents; main thread handles planning/review/commit
- Saved in memory: `feedback-use-subagent.md`

---

## Session 10 (2026-09-30) — Hero header polish, per-page backgrounds, nav bar states

### Hero header nav bar (COMPLETE)

- **Topbar merged into hero** (session 9/10 boundary): Back/Fwd, Search, Save Changes, Reload, Settings all live inside `_HeaderHeroWidget` at 186px height (38px nav row + 148px content)
- **Per-page background images**: `_HeaderHeroWidget._PAGE_IMAGE` maps view key → filename; `set_page(key)` loads lazily with pixmap cache; fallback to `stadium.webp` for missing files
  - `gui/assets/welcome.webp` — empty stadium at dusk (Welcome view)
  - `gui/assets/stadium.webp` — existing (Club view)
  - `gui/assets/squad.webp` — dawn training session (Squads)
  - `gui/assets/staff.webp` — coaches on touchline (Staff + Club Staff shares it)
  - `gui/assets/club_staff.webp` — tactics board session (Club Staff)
  - `gui/assets/shortlist.webp` — scout in stands (My Shortlist)
  - `gui/assets/reports.webp` — scouting reports desk (Player Reports)
  - `gui/assets/players.webp` — packed stadium crowd (All Players)
- **`_update_header_for_view(key)`** calls `self._hero.set_page(key)` — this is the single hook for all page switches. `_run_report()` was missing this call; fixed.
- **Progress bar** moved to bottom edge of hero (between hero and content stack) — 3px, `rgba(255,255,255,0.08)` background, accent chunk

### Nav bar button states (COMPLETE)

- **Save Changes** — dark green `#1a3d28` with subtle tinted border when enabled; dims on disabled
- **Reload** — dark amber `#3a2608` with tinted border when enabled; dims on disabled
- **Load** — blue `#2b6cb0`, always enabled
- **Save / Reload icons** — white `#ffffff` in normal state, `#3A4A58` when disabled (same as Load)
- **Search box** — `rgba(8,14,24,0.60)` enabled (hero bleeds through), `rgba(8,14,24,0.80)` on focus, `rgba(8,14,24,0.45)` disabled
- **Regular buttons** — `rgba(8,14,24,0.70)` enabled, `rgba(8,14,24,0.45)` disabled
- **Club nav button** greyed until a club is selected via search; My Shortlist always enabled

### Squad view secondary header removed (COMPLETE)

- Removed 44px `header_bar` from squad view (was showing club name + stats below hero)
- Stats (players / HGP / HGC / injured) now live in hero's right slot as quiet rich-text `_stat()` labels
- `_squad_header_bar` stored as instance attr to keep `_squad_info` / `_squad_club_label` child refs alive (prevent CTD)
- Default sort changed col 1 (INJ) → col 2 (Pos)
- HGP/HGC pill widget removed from hero right slot (was too loud; stats now in quieter inline style)

---

## Session 9 (2026-09-30) — Players filter, Reports overhaul, nav rename, club page design

### Players filter bar (COMPLETE, committed)

Replaced Min CA QLineEdit + Nation QComboBox with 5 QSpinBoxes:
- `self._players_ca_filter` — Min CA, range 0–200
- `self._players_pa_filter` — Min PA, range 0–200
- `self._players_age_min_filter` — Min Age, range 15–60
- `self._players_age_max_filter` — Max Age, range 15–60
- `self._players_dev_filter` — Min Dev, range 0–20
- `_apply_players_filter`: reads spinbox values, filters CA/PA/age/dev
- `_clear_players_filter`: uses `.setValue()` + blockSignals for all 5

### Reports view overhaul (COMPLETE, committed)

Subagent B:
- Columns now match squad: `Name | INJ | Pos | CA | PA | Dev | Age | Nation | HGP | Club | CtrE | 54 attrs` (65 total)
- INJ + Pos delegates on cols 1 + 2
- Filter controls moved to `filter_frame` row (38px) below 44px header; header row kept title + stretch only
- Default sort: `sortByColumn(2)` (Pos)

### Nav sidebar (COMPLETE, committed)

- `gui/main_window.py:1973` — "REPORTS" section label renamed to "PLAYER REPORTS"
- `gui/main_window.py:1987-1991` — "STAFF REPORTS" section added with disabled stub button (no view yet)

### Club page redesign — DESIGN CHOSEN, NOT YET IMPLEMENTED

Design A "Stadium Hero" selected. Mockup artifact: `https://claude.ai/artifact/ShmMMFy65UH5r4NZ4u4RqH`

**Layout:**
- Hero: 140px, stadium image (38% opacity) + dark gradient overlay + pitch line grid texture + club badge circle + club name + reputation stars
- KPI bar: 6 cols (Squad · Avg CA · HGP · HGC · Injured · Staff)
- 3-column body:
  - Col 1: Top Players by Avg Match Rating (green pill ≥7.0, dim plain <7.0) + Position breakdown grid
  - Col 2: Club Info + Facilities + Finances
  - Col 3: Injuries (days remaining) + Staff summary + Contracts + Homegrown counts
- Footer actions: "View Squad" + "Staff"

**Data sections requiring new binary parsing (not yet implemented):**
- Club Info: region, founded year, professional status
- Reputation: star rating (1–5)
- Facilities: training, youth, junior coaching, youth recruitment (text quality labels)
- Finances: transfer budget, wage budget, scouting budget, overall balance
- Manager: name (employment record type)
- Player match ratings: Avg Rating per player (not in current parser)

**Already parseable and ready to wire up:**
- Squad size, Avg CA, HGP count, HGC count, injury count, staff count
- Top players: sorted by CA (can swap to rating once parsed)
- Position breakdown: count per position from squad
- Injuries: name + days
- Staff: count, avg coaching attr, best CA
- Contracts: expiry dates (earliest, latest, count expiring)

**Implementation plan when ready:**
1. Reverse engineer club binary fields for reputation/facilities/finances
2. Find manager via employment records already partially parsed
3. Replace current `_make_view_club` with Design A layout
4. Stadium hero image: use a generic embedded image (data URI) for all clubs; later allow club-specific if photos found

---

## Session 8 (2026-09-29) — Major expansion

### Coaching attributes (COMPLETE)

- `find_coaching_attrs(b, people, player_ids)` in `fm_editor/gamedb.py` — parses 17 attrs per non-player staff
- Magic block: `XX 1a ea 07` at records_end+10; first byte varies per save, search suffix only
- PID verified at magic+12 (LE u32, low 16 bits must match p['id'] & 0xFFFF)
- **Section B** (magic+81, 14 bytes, terminated at `0xff`, ÷5): WwY[0] Motivating[1] Mental[2] Determination[3] Technical[4] SetPieces[5] Fitness[6] Attacking[7] Defending[8] GKShotStop[9] PeopleMgt[10] TactKnowledge[11] Negotiating[12] GKHandling[13]
- **Section A extras** (magic+37+offset, ÷5): Tactical[+33] JPA[+36] JSA[+39]
- Stored as `p['coaching']` dict
- `_COACHING_B_LABELS` list in gamedb.py matches indices above

### Staff CA/PA (COMPLETE)

- `find_staff_extras(b, people, player_ids)` in `fm_editor/gamedb.py`
- **CA at magic+33, PA at magic+35** (u8, 1-200 scale) — confirmed for Daniele Baldini (CA=143, PA=148)
- ~57% hit rate (pid_check mismatches mean neighbour's block found → safely skipped)
- Stored as `p['staff_ca']` and `p['staff_pa']`
- **Reputation, training rating, roles**: NOT located — FM-SaveLens-24 has no rep parsing either; value at end+25 is out-of-range (12k-13k). Skipped with `# ponytail:` comment.

### Injury detection (COMPLETE)

- **`b11=0x47`** = injury linked record type — confirmed via Sávio (Tottenham AMR, id=83137, ankle ligaments)
- Trail byte 0 (`b[roff+12]`) = days remaining (Sávio=5, matches "4–11 days" FM display)
- `find_injuries(b, people, player_ids)` sets `p['injured']` and `p['injury_days']`
- 27 injured players detected in test save (0.05% of 55,893 squad players)
- Edge case: some players have trail=[0,255,0,255] (days=0 = recovering); tooltip guarded by `injury_days > 0`
- Values ~204-206 may represent longer injuries stored in the same byte (unresolved)

### Player attributes (COMPLETE)

- All 54 raw attrs now in squad table columns (Cro..Cnc), `max(1, min(20, round(raw/5)))` scale
- `_ATTR_DISPLAY` in main_window.py maps index → name (54 entries)
- `_ATTR_ABBREV` provides 3-4 char column headers with tooltips via `_COL_TT`

### Contract end dates (COMPLETE)

- `find_contracts(b, people)` in gamedb.py — scans linked records for `b10=0x01, b11=0x6a`
- Encoding: `byte13 = year - 2000`, `byte14 = month (1-12)`. Returns `YYYY-MM` string.
- 54,680 players have contract dates. CtrS (start) not found — skipped.
- Column: `CtrE` (width 65px) after HGC in squad table
- Contract start: binary field not identified.

### Squad table overhaul (COMPLETE)

Current column order (index 0 onwards):
`Name | INJ | Pos | CA | PA | Dev | Age | Nation | HGP | HGC | CtrE | Cro Dri ... Cnc (54 attrs)`

- **INJ column** (index 1): dark red badge (`#8B1A1A`) when injured; tooltip "Out for X days"; sorts injured to top
- **Pos column** (index 2): numeric sort key from `_POS_SORT_ORDER`, default sort applied after populate
- Default position sort: `GK(0) DR(1) WBR(2) DL(3) WBL(4) DC(5) SW(6) DM(7) MC(8) MR(9) AMR(10) ML(11) AML(12) AMC(13) ST(14)`
- **`resizeColumnToContents` removed** from squad populate — was O(n²), replaced with fixed widths in `_configure_table_for_mode`

### Staff tables (COMPLETE)

Both global staff table and club staff table have:
- 17 coaching columns: `Atk Def Fit Mnt SPc Tac Tch WwY Det Mot PMg JPA JSA TKn Neg GKH GKS`
- 8 personality columns: `Adp Amb Loy Prs Pro Spt Tmp Ctr`
- All columns except Name/Nation have header tooltips via `_STAFF_COL_TOOLTIPS`
- `_coaching_col_map` initialised in `_make_view_staff` (runs first) so both populate functions find it

### DM badge colour

- DM changed from blue (#3A6BA8) to purple (#5A3A8A) — distinct from DC/DL/DR

### Staff detail popup (COMPLETE)

`StaffDetailDialog` (double-click staff) now shows:
- **COACHING ATTRIBUTES**: two columns (left: Attacking/Defending/Fitness/Mental/SetPieces/Tactical/Technical/WwY/PeopleMgt; right: Negotiating/GKHandling/GKShotStop)
- **MENTAL ATTRIBUTES**: Determination/Motivating/JPA/JSA/TactKnowledge from coaching dict + personality
- **ABILITY**: staff_ca and staff_pa (colour-coded via `_attr_val_color(round(val/10))`)
- **PERSONALITY**: Adaptability/Ambition/Loyalty/Pressure/Professionalism/Sportsmanship/Temperament/Controversy
- Dialog widened to 780px

### Player popup cleanup

- Removed Make HGP and Make HGC buttons from `PlayerDetailDialog` action strip
- Only "Add to Shortlist" remains

### Squads view cleanup

- Renamed "Squad" → "Squads" (nav button + breadcrumb label only; internal names unchanged)
- Removed "Clear" button from tab bar (no selection to clear in this context)
- HGP/HGC buttons now greyed out when ALL selected players already have that status

### Squad header bar (styled)

Format: `**24** players · **12** HGP · **13** HGC [· **3** injured]` (injured in red, only shown when n_inj > 0)
Uses RichText with `_stat(val, label, color)` helper inside `_populate_squad_table`.

### Status bar

Format: `● Ready · filename · 44,035 clubs, 77,966 players, X staff`

### Cache (v15)

`slim_people` now persists per entry:
- Players (`'ca' in p`): ca, pa, positions, raw_attrs, injured, injury_days, contract_end
- Staff (`'ca' not in p`): coaching, staff_ca, staff_pa

---

## Session 7 (2026-09-29) — Coaching attrs binary reverse engineering

**Coaching block binary structure** — see Session 8 above (fully implemented).

**Script**: `scripts/probe_staff_attrs.py` — run with name filter to dump coaching block

---

## Session 6 (2026-09-29) — Club staff array discovery

**`find_club_staff(b, clubs, people, abilities, names_start)`** — scans club binary records for flat u32 PID arrays:
- Byte immediately before count == `0x00`; first-PID quick reject
- Adjacent array detection: backs up 4 bytes after each valid array
- Bounded by next club's offset; returns `{club_id: [person_ids]}`
- Results: Spurs=76, Liverpool=75, ManUtd=68, ManCity=64 staff

**Key**: `b11=0x48` employment record is HGC training record NOT staff employment.

---

## Session 5 (2026-09-28) — Role weight presets

- 4 bundled presets: Equal Weight, FMScout Community, Possession-Based, Direct Play
- Settings dialog (⚙): preset dropdown, import/delete. Weight editor: per-attr spinboxes.
- `fm_editor/weights.py` + `fm_editor/weights/*.json`
- Active preset in `~/.config/fm24_editor/settings.json`

---

## What the app does

1. **Load** — file-picker for any `.fm` save; parses binary archive (~30–60s first run, instant from cache v14)
2. **Search** — type club/player name in topbar search
3. **Squads view** — Name | INJ | Pos | CA | PA | Dev | Age | Nation | HGP | HGC | CtrE | 54 attrs; default position sort
4. **Player detail** — double-click; attrs, CA/PA bars. Action strip: Add to Shortlist only.
5. **Patch** — select players, hit Make HGP or Make HGC in Squads view toolbar
6. **Reports** — Best Prospects, Wonderkids, Best in Position, Best by Role (with weight presets)
7. **Players** — all parsed players with filters; default position sort
8. **Staff** — global staff table with 17 coaching + 8 personality cols
9. **Club Staff** — per-club staff roster with same cols
10. **Staff detail** — double-click; coaching attrs, ability (CA/PA), personality

---

## UI layout (`gui/main_window.py`)

### Stack views (QStackedWidget `_main_stack`)

| Index | Key | View |
|-------|-----|------|
| 0 | `club` | Club overview |
| 1 | `squad` | Squads table (`_table`) |
| 2 | `staff` | Staff table (`_staff_table`) |
| 3 | `shortlist` | My Shortlist |
| 4 | `reports` | Scouting Reports |
| 5 | `players` | All Players |
| 6 | `club_staff` | Club Staff table |

### Squads table columns (index order)

`Name(0) | INJ(1) | Pos(2) | CA(3) | PA(4) | Dev(5) | Age(6) | Nation(7) | HGP(8) | HGC(9) | CtrE(10) | Cro(11)..Cnc(64)`

HGP foreground: col==8. HGC foreground: col==9. Nation flag font: col==7.

---

## Key classes / functions

| Symbol | Location | Purpose |
|--------|----------|---------|
| `find_coaching_attrs` | gamedb.py | 17 coaching attrs from magic block into `p['coaching']` |
| `find_staff_extras` | gamedb.py | CA/PA for staff from magic+33/+35 into `p['staff_ca'/'staff_pa']` |
| `find_injuries` | gamedb.py | `b11=0x47` linked record → `p['injured']`, `p['injury_days']` |
| `find_contracts` | gamedb.py | `b11=0x6a` byte13/14 → `p['contract_end']` YYYY-MM |
| `find_club_staff` | gamedb.py | Club binary staff PID arrays → `{club_id: [pids]}` |
| `find_employment` | gamedb.py | Employment records for managers + ex-player coaches |
| `StaffDetailDialog` | main_window.py | Staff popup: coaching/ability/personality sections |
| `PlayerDetailDialog` | main_window.py | Player popup: attrs/CA-PA bars. Add to Shortlist only. |
| `_PosBadgeDelegate` | main_window.py | Custom delegate for Pos badge column |
| `_POS_SORT_ORDER` | main_window.py | Position → sort key (GK=0..ST=14) |
| `_STAFF_COL_TOOLTIPS` | main_window.py | Short label → full name for staff table header tooltips |
| `_coaching_col_map` | main_window.py | Short label → coaching dict key (set in _make_view_staff) |
| `ParseWorker` | main_window.py | QThread — full parse pipeline |
| `is_hgc` / `patch_to_hgc` | fm_editor/patch.py | HGC detection and patching |

---

## Binary format quick-ref

See memory file: `~/.claude/projects/.../memory/fm24-binary-format.md`

- **Ability block**: `names_end+57`, gate `b[at-37]==0 && b[at-35]==0`; CA at `b[at-38]`, attrs at `b[at..at+54]`
- **HGP**: `b10=0x08, b11=0x46`
- **HGC**: `b10=0x01, b11=0x48`, bytes 0-3 = club entity ID
- **Injury**: `b11=0x47`, trail byte 0 = days remaining
- **Contract end**: `b10=0x01, b11=0x6a`, byte13=year-2000, byte14=month
- **Personality**: `b[end+17..end+25]`, 8 bytes, valid 0-20
- **Coaching magic**: `XX 1a ea 07` at records_end+10; CA at magic+33, PA at magic+35; Section B at magic+81 (14 bytes ÷5); Section A extras at magic+37+33/36/39
- **Club staff arrays**: flat u32 arrays in club record; byte before count == `0x00`; adjacent arrays use arr_end-4 backup
- **Entity ID**: club_id + 1

---

## Known limitations / TODO

| Feature | Status |
|---------|--------|
| Staff reputation / training rating / roles | Not found in binary — FM-SaveLens-24 also has no rep parsing |
| Contract start date | Binary field not identified |
| Injury days >255 | Unknown encoding — some players show 204-206 (may be multi-byte) |
| JSA label | May actually be JPP (Judging Player Potential) — needs cross-save verification |
| DM/MC sort | Currently DM(7) MC(8) — confirm ordering preference |
| Sub-squads | Live for English clubs (kind-based) and German/Spanish B teams (prefix-based) |
| Players view cap | Display capped at 3000 rows |
| ▶/▼ nav buttons | Disabled — no back/forward history |
| Player photo | Placeholder only — FM save doesn't store photos |
