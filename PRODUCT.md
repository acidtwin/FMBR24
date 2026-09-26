# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

delegated: PyQt6 desktop application with QSS styling; Flask-free since this is a local tool with no networking needed.

## Users

FM24 players (Football Manager 2024) who want to edit squad registration data in save files — specifically making players count as homegrown for Premier League squad registration. Used solo, on Linux, typically during or between FM sessions.

## Product Purpose

A desktop GUI tool that parses FM24 binary save files, shows any club's squad with their current homegrown status, and lets the user patch selected players to count as homegrown — without requiring any paid editor software (FMRTE etc.).

## Positioning

The only free, open, Linux-native FM24 homegrown editor that shows you the squad first and lets you decide, rather than requiring you to know player names in advance.

## Operating Context

- User has FM24 running (or closed) on Linux via Steam/Proton
- Save files are large binary archives (~180–220 MB) that require decompression
- First parse of a save is slow (~30–60 sec); subsequent runs can cache results
- User wants to load a specific save file, search for a team, review their squad, then patch chosen players and save to a new file

## Capabilities and Constraints

- Read and write FMF (FM archive format) files: zstd-compressed members, binary index
- Parse game_db.dat: name pools, club structs, squad membership, player registration records
- Detect homegrown status: presence of England secondary nation qual record (n=0x8b, b10=0x08, b11=0x46)
- Patch in-place (no byte insertion, no file-size change) to avoid breaking internal structure
- Must support: file picker for any .fm save, team search, per-player HGP toggle, write to new file
- Caching: save parse results to disk keyed by file mtime to avoid re-parsing every run
- Platform: Linux desktop, PyQt6

## Evidence on Hand

- Working Python backend scripts in /tmp scratchpad (fm24_editor.py, fm24_parse.py)
- Verified against a real 188 MB FM24 save: correctly identifies 5/25 Tottenham players as homegrown
- Confirmed patch approach works: in-place b11=0x46 n-byte rewrite + optional b11=0x40→0x47 flip

## Product Principles

1. Show first, decide after — display the full squad before committing any change
2. Non-destructive — always write a new file, never overwrite the original
3. Speed through caching — the slow parse runs once; subsequent opens are instant
4. No friction — file picker, type a team name, click players, hit patch: four steps maximum
