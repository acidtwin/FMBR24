# FM24 Homegrown Editor — Handover

**Last updated:** 2026-09-27
**Project:** `/run/media/acidtwin/Gaming SSD 1/Claude Code Projects/FM-Save-Editor`

---

## Current state

Working FM24 save editor with full FM24-skin UI. Tested against a real Tottenham 2026-27 save.

All changes committed on `master`. No uncommitted work.

---

## What the app does

1. **Load** — file-picker for any `.fm` save; parses binary archive (~30–60 s first run, instant from cache)
2. **Search** — type a club name in the topbar search to load their squad, or a player name to find them
3. **Squad view** — shows club squad with Pos (colored badge), CA, PA, Dev Rate, Age, Nation (flag emoji), HGP, HGC columns
4. **Player detail** — double-click a player to open their profile modal (attributes, CA/PA bars, HGP/HGC pills, Make HGP / Make HGC actions)
5. **Patch** — select players in squad view, hit Make HGP or Make HGC; saves to a new file via file dialog (default: `SaveName-Edited-DATE.fm`)
6. **Save Changes** — topbar button writes current binary state to file (no patching)
7. **Reports** — Scouting → Reports sidebar section; accordion view with Best Prospects, Wonderkids, Best in Position (position picker), Best by Role (coming soon)
8. **Players** — Scouting → Players sidebar section; shows all parsed players sorted by CA with name/pos/nation/min-CA/nation filters; player search results land here

---

## UI layout (`gui/main_window.py`)

### Stack views (QStackedWidget `_main_stack`)

| Index | Key | View |
|-------|-----|------|
| 0 | `club` | Club overview (name, player/HGP/HGC counts) |
| 1 | `squad` | Squad table (QTableWidget `_table`) |
| 2 | `staff` | Staff (stub) |
| 3 | `shortlist` | My Shortlist (stub) |
| 4 | `reports` | Scouting Reports accordion |
| 5 | `players` | All Players view (QTableWidget `_players_table`) |

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
| `ParseWorker` | main_window.py | QThread — parses .fm archive |
| `PatchWorker` | main_window.py | QThread — patches HGP/HGC or `mode='save_only'` |
| `PlayerDetailDialog` | main_window.py | Player profile modal (attrs, CA/PA bars, action strip) |
| `_PosBadgeDelegate` | main_window.py | Custom QStyledItemDelegate for Pos column badges |
| `_attr_val_color(v)` | main_window.py | Returns color for attr value (gold ≥17, green ≥16, …) |
| `_NATION_FLAG` | main_window.py | nation_id → flag emoji mapping |
| `_POS_BADGE_COLORS` | main_window.py | pos string → (bg, fg) for badge delegate |
| `_DOT_SEQ` | main_window.py | `[1,2,3,4,3,2]` ping-pong dot animation |
| `NATIONS` | main_window.py | nation_id → nation name (35 entries) |
| `POSITIONS` | main_window.py | FM24 position strings list |
| `find_club_entity_id` | fm_editor/patch.py | Finds club entity ID from b11=0x6a records |
| `is_hgc` | fm_editor/patch.py | Checks HGC status from training records |
| `patch_to_hgc` | fm_editor/patch.py | Patches/inserts HGC training record |

---

## Known limitations / UI stubs

| Feature | Status |
|---------|--------|
| Staff view | Stub — shows placeholder text |
| My Shortlist | Stub — wire up Add to Shortlist from player modal |
| Best by Role report | Coming soon — role classification not yet implemented |
| ▶ / ▼ navigation buttons | Disabled (greyed) — no back/forward history yet |
| Right tab nav in player modal | Only Profile tab active; Transfer/Positions/Ratings are future |
| Squad number (#) column | Not implemented — mockup had it, excluded by design |
| Sub-squads (U21/B team) | Sidebar Players squad-version tabs — First Team tab exists, sub-teams need squad parsing to identify them |
| Players view: load all | Currently loads all people with CA data (no explicit limit enforced in filter; display caps at 3000 rows); slow on first open for large saves |
| HGP/HGC patching from cache | Disabled — requires binary `b` in memory; user must Load (not use cached version) |
| Player photo | Placeholder person icon; FM save doesn't store player photos |

---

## Binary format quick-ref

See memory file: `~/.claude/projects/-run-media-acidtwin-Gaming-SSD-1-Claude-Code-Projects-FM-Save-Editor/memory/fm24-binary-format.md`

- **Ability block**: scanned from `names_end + 57`, gate at `b[at-37]==0 && b[at-35]==0`; CA at `b[at-38]`, attrs at `b[at..at+54]`
- **HGP**: secondary nation record `b10=0x08, b11=0x46`
- **HGC**: training record `b10=0x01, b11=0x48`, bytes 0-3 = club entity ID (LE u32)
- **Personality**: `b[end+17..end+25]` in person record, 8 bytes 1-20

---

## Next steps / ideas

- Wire **Add to Shortlist** in player modal → My Shortlist view
- **Back/forward** navigation history (`_nav_history` stack)
- **Sub-squad tabs** (U21, B team) — needs squad grouping by team entity ID in parser
- **Best by Role** report — map positions to FM roles, rank by relevant attributes
- **Player photo** — if FM24 image packs can be located on disk, load by player ID
- **Bulk export** — export squad CSV
- **Season update** — `FM_SEASON_YEAR` is hardcoded to 2024; could derive from save filename or header
