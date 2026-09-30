# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

delegated: PyQt6 desktop application with QSS styling; Flask-free since this is a local tool with no networking needed.

## Users

FM24 players (Football Manager 2024) who want to look inside their save: browse any club's squad and staff, scout the whole database, check save metadata, and optionally patch players to count as homegrown (Premier League squad registration). Used solo, on Linux, typically during or between FM sessions.

## Product Purpose

FM Backroom 24 (FMBR24): a desktop GUI that parses FM24 binary save files and shows what the game hides or buries in menus — club overview, squads with all attributes, injuries and contracts, staff (coaching attributes, CA/PA, personality), scouting reports over every player, a shortlist, and save info — plus homegrown (HGP/HGC) patching, without paid editors (FMRTE etc.). Unofficial fan tool; not affiliated with Sports Interactive / SEGA.

## Positioning

The free, open, Linux-native FM24 save browser: look first, then decide. Read-mostly with one focused edit (homegrown); no need to know player names in advance.

## Operating Context

- FM24 runs via Steam/Proton on Linux; saves are large binary archives (~180-220 MB), zstd members
- First parse of a save is slow (~60 s); results are cached by file mtime (cache read-back currently not wired up, see HANDOVER)
- Flow: load a save, land on Save Info, search a club/player/staff name, review, optionally patch, then Save Changes (2 backups, then overwrite in place)
- Roadmap: 1.0 polish, then Flatpak and Windows builds

## Capabilities and Constraints

- Read/write FMF archives (zstd members, binary index); FM24 saves only (FM23 fails)
- Parse game_db.dat: names, clubs, squads, people, ability blocks, personality, contracts, injuries, coaching attributes, staff CA/PA, club staff arrays
- Save Info: game name, dates, game time/version, database version/changes, manager and club, nations/leagues, start date. Rows with no data are hidden; database size, start nation, future transfer mode, editor and manageable-teams are not decodable yet
- Club page: squad KPIs, top players, injuries, contracts, homegrown counts; unparsed data (reputation, facilities, finances, manager rating) is marked PENDING
- Scouting reports: Best Prospects, Wonderkids, Best in Position, Best by Role (weight presets); All Players view; Staff and Club Staff tables; Player and Staff Shortlists; shared Quick Filters bars
- HGP: secondary nation qualification record `b10=0x08, b11=0x46`. HGC: training record `b10=0x01, b11=0x48` (bytes 0-3 = club entity id). Patches apply to the in-memory `game_db.dat`; Save Changes (`fm_editor/savefile.py`) writes it back
- Search routes club -> Club page, player -> Players, staff -> Staff
- Transfer values, player photos and staff reputation are not stored in the save
- Platform: Linux desktop, PyQt6; dark FM24-style skin (QSS)

## Evidence on Hand

- Verified against real FM24 saves (Tottenham 2026-27, 188 MB): 5/25 homegrown detected correctly, patch approach confirmed (in-place b11=0x46 rewrite + optional b11=0x40 to 0x47 flip)
- Save Info fields checked against the in-game Game screen; unit-style checks in `tests/`

## Product Principles

1. Show first, decide after: display before committing any change
2. Recoverable: Save Changes keeps two rolling backups (`<save>.fm.bk1`, `.bk2`) and verifies a temp file before atomically replacing the save
3. Speed through caching: the slow parse should run once
4. No friction: pick a save, type a name, see the answer; patching stays four steps
5. Never fabricate data: hide it, or mark it PENDING
