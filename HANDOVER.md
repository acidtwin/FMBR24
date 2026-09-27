# FM24 Homegrown Editor — Session Handover

**Date:** 2026-09-27  
**Project:** `/run/media/acidtwin/Gaming SSD 1/Claude Code Projects/FM-Save-Editor`

---

## What was done this session

### HGC (Homegrown at Club) patching — COMPLETE

Added full HGC support to complement existing HGP (Homegrown Player / nation) patching.

**Binary format discovered:**
- HGC status = training record with `b10=0x01, b11=0x48, bytes 0-3 = club entity ID` (little-endian u32)
- Club entity ID found from `b11=0x6a` (employment) records — most common val0 across squad
- Entity ID = `club_id + 1` in practice (e.g. Tottenham club_id=492, entity_id=493)
- ~3/25 players may have NO b11=0x48 record at all → insertion required (new 16-byte record)

**Files changed:**

`fm_editor/patch.py` — added:
- `find_club_entity_id(b, squad)` — finds entity ID from b11=0x6a records
- `is_hgc(b, person, club_entity_id)` — checks HGC status
- `patch_to_hgc(b, persons_desc, club_entity_id)` — patches HGC; overwrites first b11=0x48 record OR inserts new one. **Must receive persons sorted descending by `end` offset** when insertions may occur.

`gui/main_window.py` — added:
- HGC column in squad table (col 8, after HGP col 7)
- "Select Non-HGP" / "Select Non-HGC" buttons (replaced old "Select All Non-HGP")
- "Make HGP" / "Make HGC" buttons (replaced old "Make Selected Homegrown")
- `_club_entity_id` stored on window when squad loaded (requires `b` in memory — not available from cache)
- HGC count shown in squad info label
- `PatchWorker` extended: `mode='hgp'|'hgc'`, `club_entity_id`; updates `m['p']` if bytearray grew from insertions

**HGC buttons are greyed out** when save loaded from cache (no `b` in memory). User needs "Load / Reload" — same constraint as HGP patching.

### CLAUDE.md reorganisation — COMPLETE
Moved 661-line CLAUDE.md from repo root to `BuildingIdeasBoard/CLAUDE.md`.
Root CLAUDE.md is now a 10-line stub. **Takes effect next session** — FM-Save-Editor sessions will no longer load the Building Ideas Board context, freeing ~half the context window.

---

## Abandoned work (previous sessions)

**AFE shortlist decryption** — investigating AES-128-GCM key used in FM24 `.fmf` shortlist files via FMGenieScout.exe reverse engineering. Got as far as:
- Full AFE archive format documented
- Key derivation traces to Windows CryptAPI via IAT at VA 0xc035a4
- Key input = output filename string, processed via `CryptDeriveKey` equivalent
- **Stopped** — user decided it was taking too long; pivot to HGC instead

---

## Current state

Code is working and tested against a real FM24 save (2026-27 season).  
HGC detection correctly identifies academy products (Archie Gray, Brandon Austin, Callum Olusesi, Lucas Bergvall at Tottenham).

**Not yet committed** — the HGC changes to `patch.py` and `main_window.py` are edited but not git-committed.

---

## Possible next steps

- Git commit the HGC changes
- Test HGC patching end-to-end (patch a player, load save in FM24, verify squad registration screen)
- Memories: existing memory files keyed to the old root path; FM24 binary format memory at `~/.claude/projects/-run-media-acidtwin-Gaming-SSD-1-Claude-Code-Projects/memory/fm24-binary-format.md` — update or move to FM-Save-Editor key if needed
