<p align="center"><img src="resources/icon.png" width="128" alt="FM Backroom 24 icon"></p>

# FM Backroom 24 (FMBR24)

PyQt6 desktop tool for browsing Football Manager 2024 save files on Linux, with one focused edit: homegrown (HGP/HGC) patching.

- Save Info and Club overview (reputation, stadium, league position, finances, contracts, injuries)
- Squads with full attributes; club staff; scouting tables over every player and staff member in the database
- Reports (Best Prospects, Wonderkids, Best in Position, Best by Role) with quick filters, and separate player and staff shortlists
- Detailed player window: ability and potential (stars or numbers), attribute radar, Full Potential projection, traits, season stats, career history
- Homegrown patching: queue HGP (nation) or HGC (club) for your own club's players, then Save Changes: a verified temp file, two rolling backups (`.bk1`/`.bk2`), atomic replace, automatic reload

## Run

```bash
pip install -r requirements.txt   # PyQt6, zstandard, numpy
python main.py
```

Unofficial fan tool for Football Manager 24 — not affiliated with or endorsed by Sports Interactive or SEGA. Football Manager and FM are trademarks of their respective owners.
