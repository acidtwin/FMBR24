# Product

<!-- impeccable:product-schema 1 -->

## Platform

Linux desktop (a Windows .exe build is planned for 1.0)

## Stack

delegated: PyQt6 desktop application with QSS styling; local tool, no networking.

## Users

FM24 players (Football Manager 2024) who want to look inside their save: browse any club's squad and staff, scout the whole database, read a detailed player sheet, check save metadata, and optionally patch players to count as homegrown (Premier League squad registration). Used solo, on Linux, typically during or between FM sessions.

## Product Purpose

FM Backroom 24 (FMBR24): a desktop GUI that parses FM24 binary save files and shows what the game hides or buries in menus, without paid editors (FMRTE etc.). Read-mostly, with one focused edit (homegrown HGP/HGC). Unofficial fan tool; not affiliated with Sports Interactive / SEGA.

## Positioning

The free, open, Linux-native FM24 save browser: look first, then decide. No need to know player names in advance.

## Operating Context

- FM24 runs via Steam/Proton on Linux; saves are large binary archives (~180-220 MB), zstd members
- A full parse takes roughly 15 s (reported, not re-timed); the parse cache (path + mtime + size) makes a normal Load about 2 s, Reload always re-parses
- Flow: load a save, land on Save Info, search a club/player/staff name, review, optionally queue HGP/HGC, then Save Changes (two rolling backups, verified temp file, atomic replace), after which the save reloads and the view is restored
- Roadmap: 1.0 polish, then a Flatpak build and a Windows .exe (1.0). Designed but not built yet: a goal-net header texture, a solid sidebar icon set (`docs/DESIGN-BACKLOG.md`)
- Distribution: public repo `acidtwin/FMBR24` on GitHub (alpha, source only, run with `python main.py`)

## What exists now

- FMF archive read/write (zstd members); FM24 saves only (FM23 fails)
- Save Info: game name, dates, game time/version, database version, manager and club, nations/leagues. Rows with no data are hidden; database size, start nation, future transfer mode, editor and manageable teams are not decodable yet
- Club page: squad KPIs, top players, injuries, contract expiry counts (against the in-game date), homegrown counts, reputation stars, stadium, league position, finances, scouting budget (human club); values the save does not give us are hidden or marked PENDING (Settings option)
- Squads (full attributes, injuries, contracts), Club Staff, Players and Staff scouting tables over the whole database, Player and Staff Shortlists, quick filters
- Pictures from the user's own installed graphics packs (read-only, nothing bundled, each switchable in Settings): faces (player window, staff window, list rows), club badges (player window, Save Info, page headers, Club column of the lists), nation crests (Nation column) and competition logos (Club page); anything a pack lacks falls back to text. A kit-picture lookup exists in code but no screen uses it
- CA / PA / Dev Rate as stars or raw numbers (Settings > Ability display) in the player window and in the Squads, Reports, Players and Player Shortlist lists
- Player reports: Best Prospects, Wonderkids, Best in Position, Best by Role (weight presets; a minimum position-familiarity filter, default 14). Staff Reports is a stub
- Player window: header with CA/PA/Dev Rate (stars or numbers, Settings), tabs Profile, Contract & Transfer (with a value-by-age trend chart: an estimate anchored on the stored value, not a price), Positions, Player Role Rating (role percentages per position, pitch view; the role lists are not yet verified in game), Training (recommended traits), History; six-axis radar, Current | Full Potential projection (display only), season stats, traits and personality, texture themes. General Rating is a placeholder; clicking the player name copies it. Familiarity and foot words use the app's own wording (e.g. 'Ineffective'), not the game's
- Compare Players page (sidebar): two searchable selectors (whole save, Recent / Squad / Shortlist lists), overlaid radar (Overview 6 axes | Detailed 12 / 11 axes), attribute table with who is ahead, key facts incl. transfer value; `Compare to...` in the player window
- HGP (secondary-nation record) and HGC (training record) patching: pills in the player window, Make HGP / Make HGC in Squads, queued then written by Save Changes; only for human-managed clubs
- Search routes club -> Club page, player -> Players, staff -> Staff; Back/Forward history; Settings page; page icons in each header and in the sidebar; a vector app logo; busy veil ('Saving' / 'Reloading') during Save/Reload; a Welcome-header glow during a first load
- Not stored in the save: player pictures (they come from the user's own packs), staff reputation, club facilities/region/founded, contract bonuses/clauses, hidden player reputation. Transfer data: 'Not for Sale' (value 300,000,000) and 'On loan from <club>' are shown in the Transfer panel; asking price/listing status/contract type are not found yet (next: controlled experiment saves)
- Platform: Linux desktop (Windows .exe planned at 1.0), PyQt6, dark FM24-style skin (QSS)

## Evidence on Hand

- Save Info, squads, finances, season stats, ages, reputation/league positions, height/weight, contracts, injuries and most trait bits were checked against in-game screens (Tottenham 2026-27 save); HGP insert verified in game (Montoro). In-game load of a save with an HGC insert is not verified yet
- 45 plain-script checks in `tests/`; real-save tests read frozen copies of the save, never the live one; details and open items in `HANDOVER.md`

## Product Principles

1. Show first, decide after: display before committing any change
2. Recoverable: Save Changes keeps two rolling backups (`<save>.fm.bk1`, `.bk2`) and verifies a temp file before atomically replacing the save
3. Speed through caching: the slow parse should run once
4. No friction: pick a save, type a name, see the answer; patching = queue, then Save
5. Never fabricate data: hide it, or mark it PENDING
