<p align="center"><img src="resources/icon.svg" width="128" height="128" alt="FM Backroom 24 icon"></p>

<h1 align="center">FM Backroom 24 (FMBR24)</h1>

<p align="center">Scout, browse and lightly edit your Football Manager 2024 saves on Linux, in a desktop app that looks the part.</p>

<p align="center">
  <img alt="Python 3.12" src="https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white">
  <img alt="PyQt6" src="https://img.shields.io/badge/GUI-PyQt6-41CD52">
  <img alt="Linux" src="https://img.shields.io/badge/platform-Linux-FCC624?logo=linux&logoColor=black">
  <img alt="Status: alpha" src="https://img.shields.io/badge/status-alpha-orange">
  <img alt="FM24 saves only" src="https://img.shields.io/badge/saves-FM24%20only-6b21a8">
</p>

<p align="center"><a href="docs/screenshots/player-profile.png"><img src="docs/screenshots/player-profile.png" width="720" alt="The FMBR24 player window, Profile tab"></a></p>

## Why this exists

There are very few scouting and editing tools for Football Manager on Linux. FMBR24 aims to be a Swiss-army knife for FM24 on Linux: scouting, save viewing and a little editing, with a UI that is a pleasure to use rather than a pile of spreadsheets.

You open a save, and the app reads it directly. No game running, no paid tool, no need to know a player's name in advance: look first, then decide.

## Features

**Scouting and reports**
- Players and Staff tables covering every person in the database (about 78,000 players and 50,000 staff in a typical save), with quick filters (name, position, CA, PA, age, development rate)
- Player Reports: Best Prospects, Wonderkids, Best in Position, Best by Role (role weight presets, editable and importable in Settings; a minimum position-familiarity filter)
- Player and Staff Shortlists

**Squad and club**
- Save Info: game name and dates, game version, database version, manager and club, nations and leagues
- Club page: squad KPIs, top players by average rating, contract expiries, injuries, reputation, stadium, league position, finances, scouting budget
- Squads with full attributes, contracts and injuries (first team, U21, U18) and a Club Staff list

**Player window**
- Profile: attributes by group, an attribute radar, footedness, personality, traits, season stats and fitness
- Role ratings as a percentage per position, with a pitch view
- Value-by-age trend chart (an estimate anchored on the stored market value, not a price)
- Positions: a rating for every position, shown as a list and on a pitch
- Contract & Transfer: contract dates and wage, market value, Not for sale / On loan from (parent club) status
- Career history in the game's Career Stats layout (club, fee, nation, division, apps, goals, assists, player of the match, average rating, totals), recommended traits, and a Current / Full Potential projection (display only)
- CA and PA as stars or raw numbers, Development Rate as five pips, stars or raw numbers (Settings), in the player window and in every player list; Best by Role shows a rating ring. The raw value is always the tooltip and sorting is always by the number
- Selectable player window theme (Steel, Pitch lines, Floodlit, Plain) and a faint random stadium photo behind the player and staff windows
- Face pictures from your own installed facepack (for example DF11): the player window header and the staff window show the same face the game does, looked up by the person's UniqueID from the pack's `config.xml`. Auto-detects your FM24 folder, reads it read-only, builds its index in the background (about half a second for 200,000 pictures), and can be switched off in Settings. Nothing is bundled: bring your own pack. Generated players (newgens) only show a face when your facepack tool has written a config for them, the same as in the game
- Club badges from your own installed logo pack (for example FMG Standard Logos): shown before the club name in the player window, on Save Info and in the Club, Squads and Club Staff headers. Same read-only lookup as the face pictures, switch off in Settings; the club badge is found through the club's UniqueID, using the game's install database when available. Nothing is bundled: bring your own pack
- Pictures in the lists: Squads, Player Reports, Players, Player Shortlist and the staff lists show the person's face before the name, the club as its badge (hover for the club name, sorting stays by name) and the nation as the nation's picture from your logo pack (hover for the name); anything the packs do not have falls back to the plain text, so no information is lost. The Club page shows the league's competition logo. All of it is read-only, built from your own installed packs, off-thread and lazily decoded for the visible rows only, and switchable in Settings (Show face pictures / club badges / nation flags)
- Kit lookup from your installed kit packs (`graphics/kits/<pack>`, home / away / third): available to the code, no screen uses it yet

**Compare players**
- A Compare Players page (sidebar, in the SCOUTING section after Staff): pick two players from searchable selectors (type any name in the save, or choose from your recently viewed players, your squad or your shortlist) and see them on one overlaid radar with an attribute table that shows who is ahead and by how much, the number of attributes each one wins, and key facts (age, contract, transfer value or Not for sale, wage, size, traits). Goalkeepers are only compared with goalkeepers
- The radar has an Overview (6 axes) and a Detailed mode (12 outfield / 11 goalkeeper axes such as shooting, ball control, passing, aerial, pace), Current or Full Potential, stars or raw numbers like everywhere else (Settings)
- `Compare to...` in the player window opens the page with that player as player A; the last 8 players whose window you opened are remembered per save

**Editing**
- Homegrown flags (HGP / HGC) for the players of your own club: queue them from the player window or the Squads toolbar, then press Save Changes
- Save writes a verified temp file, keeps two rolling backups (`.bk1`, `.bk2`), replaces the save atomically and reloads it

**Quality of life**
- Search box with autocomplete for clubs, players and staff, Back / Forward history
- After a Save or Reload you land back on the same page, filters, sort and selection
- A parse cache makes loading the same save again quick
- Player window texture themes, header texture (diamond net by default, or square-knot, perspective, honeycomb or the old pitch lines), landing page and other options in Settings

## Screenshots

Click a picture for the full size. They are generated from a real save with `scripts/make_screenshots.py`.

<table>
  <tr>
    <td width="50%"><a href="docs/screenshots/save-info.png"><img src="docs/screenshots/save-info.png" alt="Save Info"></a><br><sub>Save Info</sub></td>
    <td width="50%"><a href="docs/screenshots/club.png"><img src="docs/screenshots/club.png" alt="Club page"></a><br><sub>Club</sub></td>
  </tr>
  <tr>
    <td><a href="docs/screenshots/squads.png"><img src="docs/screenshots/squads.png" alt="Squads with a queued HGP change"></a><br><sub>Squads, with HGP / HGC badges and one queued change (yellow)</sub></td>
    <td><a href="docs/screenshots/scouting-players.png"><img src="docs/screenshots/scouting-players.png" alt="Scouting: all players"></a><br><sub>Scouting: all players</sub></td>
  </tr>
  <tr>
    <td><a href="docs/screenshots/player-report.png"><img src="docs/screenshots/player-report.png" alt="Player report: Best Prospects"></a><br><sub>Player report: Best Prospects</sub></td>
    <td><a href="docs/screenshots/settings.png"><img src="docs/screenshots/settings.png" alt="Settings"></a><br><sub>Settings</sub></td>
  </tr>
  <tr>
    <td><a href="docs/screenshots/player-profile.png"><img src="docs/screenshots/player-profile.png" alt="Player window: Profile"></a><br><sub>Player window: Profile (radar, footedness, attributes)</sub></td>
    <td><a href="docs/screenshots/player-contract.png"><img src="docs/screenshots/player-contract.png" alt="Player window: Contract and Transfer"></a><br><sub>Player window: Contract &amp; Transfer (value by age)</sub></td>
  </tr>
  <tr>
    <td><a href="docs/screenshots/player-positions.png"><img src="docs/screenshots/player-positions.png" alt="Player window: Positions"></a><br><sub>Player window: Positions</sub></td>
    <td><a href="docs/screenshots/player-role-rating.png"><img src="docs/screenshots/player-role-rating.png" alt="Player window: Role Rating"></a><br><sub>Player window: Role Rating</sub></td>
  </tr>
  <tr>
    <td><a href="docs/screenshots/compare.png"><img src="docs/screenshots/compare.png" alt="Compare players"></a><br><sub>Compare players (Detailed radar)</sub></td>
    <td><a href="docs/screenshots/player-history.png"><img src="docs/screenshots/player-history.png" alt="Player window: History"></a><br><sub>Player window: Career history</sub></td>
  </tr>
  <tr>
    <td><a href="docs/screenshots/player-training.png"><img src="docs/screenshots/player-training.png" alt="Player window: Training and recommended traits"></a><br><sub>Player window: Training (recommended traits)</sub></td>
    <td><a href="docs/screenshots/report-best-by-role.png"><img src="docs/screenshots/report-best-by-role.png" alt="Player report: Best by Role"></a><br><sub>Player report: Best by Role (rating ring)</sub></td>
  </tr>
</table>

## Status and roadmap

FMBR24 is **alpha** and supports **FM24 saves only**. It is built and tested on Linux first.

- Transfer data (asking price, transfer-listed and loan-listed status; loan end dates) is still being reverse-engineered, so those fields show as PENDING
- A General Rating tab is planned for the player window
- The staff window is due a redesign
- At 1.0: a Flatpak package and a Windows `.exe`

## Feature requests and bugs welcome

This is a young project and feedback shapes it. [Open an issue](https://github.com/acidtwin/FMBR24/issues/new/choose) for a bug report or a feature request.

For a bug, please include:
- what you did and what you expected to happen
- your FM24 game version (shown on the Save Info page) and the size of the save
- the crash log, `/tmp/fm_editor_debug.log`, if the app crashed or showed an error

Please do not attach your save to a public issue unless you are happy for anyone to download it. It holds your whole game database.

## Run

```bash
pip install -r requirements.txt   # PyQt6, zstandard, numpy
python main.py
```

Python 3.12 on Linux. Click Load and pick your FM24 save (`.fm`). Saves made by Football Manager 2024 under Steam and Proton are the tested case.

## Safety

FMBR24 reads your save and, only when you press Save Changes, writes the homegrown flags you queued. To keep that safe:

- It only edits homegrown flags, and only for the players of your own club
- Every save is written to a temp file and checked before it replaces anything
- It keeps two rolling backups next to your save (`.bk1`, the file before the last save, and `.bk2`, the one before that). Nothing is overwritten without them
- It refuses to save if the file changed on disk since you loaded it
- Saves edited this way (HGP and HGC flags, including inserted records) have been loaded in FM24 and showed the new homegrown tags correctly in the cases tested. It is alpha: keep those backups

Keep your own backups too. This is alpha software and FM saves are big, binary and undocumented.

## Inspired by

- **FMRTE.** I tried to buy the FM24 version for about a month, but the site kept looping or failing and support did not reply. So I decided to build my own. It is a well-known tool and I am sure it works fine for many people
- **FM Genie Scout / FM Scout.** A huge inspiration, especially its transfer and role-rating style screens
- <!-- [TODO: name of the Linux FM editor project] --> An earlier Linux FM save-editing project showed it was possible, which is why I started

Unofficial fan tool for Football Manager 24 — not affiliated with or endorsed by Sports Interactive or SEGA. Football Manager and FM are trademarks of their respective owners.
