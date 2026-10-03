# Design backlog: mockups to come back to

Designed surfaces that are not (fully) built or decided yet. Rule: a mockup is approved by the user BEFORE any app code (`CLAUDE.md`, mockup first; translate mechanically, never by eye). Open the mockups straight from disk (`file:///.../mockups/<name>.html`); no web server; the user tests them at http://localhost:8792 by refreshing. State of the app: `HANDOVER.md`.

## 1. Compare players

- **Status:** mockup APPROVED as the direction ("very good so far"); the user wants to come back to it. NOT built: no `Compare` code exists in `gui/` or `fm_editor/`.
- **Mockup:** `mockups/compare-players.html` (sample players are fictional). Views via URL: `?pair=out|gk|young|veteran`, `?nums`, `?pot`, `?pick`, `?swap`, `?noface`, `?min`, `?bare=1`. The header comment of the file is the spec (launch flows, geometry, QPainter porting notes, data needs).
- **Direction:** variant A = overlaid radars of both players plus the full attribute table; ONE layout. A percentile "fingerprint pizza" view was tried and REMOVED by user decision (so were duels, similarity and peer data).
- **Decisions recorded:**
  - 'Attributes won' counts ALL attributes equally (no role weighting); Footedness is not counted; tooltip says so.
  - A goalkeeper's outfield Technical group is hidden in the table (still feeds the radar axis Distribution); a keeper is only compared with keepers.
  - Lists: exactly 2 selected rows open Compare directly (toolbar `Compare`, enabled only for 2 rows); 1 selected row opens the picker with that row as A.
  - Identity colours: A sky blue `#52B0FF` (solid outline, circle marker), B orchid `#D77CFF` (dashed outline, diamond marker), tokens `--a` / `--b`; no tier colour is blue or violet.
  - Launch: player window action strip gets a left-group button `Compare with...` (Close stays last); also from the lists (above).
  - Current | Full Potential segmented control sits in the header of the left panel and drives radar, difference bars and table.
  - Buttons of the window: `Swap sides`, `Change player B...`, stretch, `Add both to Shortlist`, `Close` (CLOSE LAST). Picker dialog: [Compare] [Cancel] (Cancel last).
  - Stars rule applies only to the header CA/PA boxes (`ability_display`, raw number in the tooltip); no new Settings key.
- **Data needed:** only what the player window already has: 54 attributes (current, and `potential.project_attrs` for Full Potential), position, nation, club, age, CA/PA, contract end, value, wage, height/weight, trait count (`player_extra_data` in `gui/player_window.py`). No new parsing, no `_CACHE_VERSION` bump.
- **Build plan (suggestion):**
  1. `gui/compare_window.py`: `CompareWindow(QDialog)` 1122x760 (min 1062x640), header (two player panels, VS), left panel radar + 'Difference by group', right panel 'Attributes' (three columns, winner arrow) + 'Key facts' strip, action strip. Reuse the player-window theme registry (`gui/pw_themes.py`) for the header/strip.
  2. Radar: `RadarWidget` (`gui/pw_widgets.py`) is single-dataset and fixed 204x176 (R 40); the mockup needs R 106 at 358x336 and two overlaid polygons (draw B first, then A; markers circle / diamond). Generalise it (datasets + size) or add a sibling widget; keep `RADAR_OUT` / `RADAR_GK` axis maths and `test_radar_axes.py` green.
  3. Picker: QDialog 540 wide, search box via the existing `_SearchSuggest` (`gui/search_suggest.py`, players only), 'same position first' ordering, chips 'Outfield players only' / 'Goalkeepers only', 'From list selection (n)', 'Shortlist'; Enter = Compare. Same dialog serves `Change player B...`.
  4. Wire: button in the player-window action strip; list toolbars (Squads, Players, Reports, Shortlist) with the 2-row / 1-row rule.
  5. Tests (plain scripts): attributes-won counting (Footedness and GK Technical excluded, inverted attributes as 21-v), radar axes for both datasets, 2-row vs 1-row launch, picker filtering; headless `.grab()` PNG check against the mockup values.

## 2. Goal-net header texture

- **Status:** four variants drawn; the user has NOT chosen yet. Nothing built (the app header texture is still the plain pitch grid `_grid_lines` in `gui/main_window.py`).
- **Mockup:** `mockups/header-net.html`; `?v=a|b|c|d` (`g` = the current pitch grid, reference), `&glow` (animate the loading glow), `&glow=peak`, `&bare=1`, `&k=` strength, `&w=` header width. The file header comment holds the generator pseudocode and constants.
- **Variants:** A diamond mesh (classic netting); B square-knot net (sagging orthogonal mesh; the previous agent's RECOMMENDATION); C perspective net hanging in the goal mouth (radial mask + corner shadow); D honeycomb + light sweep + post/crossbar corner.
- **Build notes:** one function `net_geometry(variant, w, h)` returns strands, knots, mask, deco. Cache ONE `QPixmap` per `(w, h, dpr)` in the slot of `_g_cache` (as `_glow_layers` does); `paintEvent` becomes one `drawPixmap`. The loading glow (`HERO_GLOW`) reuses the same strand path/mask: core and halo pixmaps stroke the same path in the tint `QColor(150,130,255)` and re-apply the mask (`DestinationIn`); halo widths become per-net (8, 4 px for the finer nets), peak 0.10 / period 3400 unchanged. Replaces `_grid_lines` as the single source of the texture and the glow mask. Net alpha never above about 0.08 white (title/subtitle legibility). Test: extend `test_hero_glow.py` and take offscreen PNGs of the Welcome and Club headers.

## 3. Sidebar solid icon set

- **Status:** waiting for the user to generate the icon sheet. Not built. The header badge and sidebar keep the CURRENT line icons (`resources/icons/pages/*.png`, 18 files) meanwhile.
- **Wanted:** new solid-style (filled) icons for the sidebar. Palette: purple `#6933BD`, highlight `#735CE4`, off-white `#ECEAF2`, green `#4caf82` spark; pentagon motif.
- **Image prompt** (already given to the user): ONE 18-icon sheet, 6 columns x 4 rows of 256 px cells on a flat `#14151A` background, 1536x1024 image.
- **What the build needs:** `scripts/cut_icon_sheet.py` today cuts a 3x2 sheet of 512 px cells with TWO ink colours (off-white or purple) by colour un-mix. A v2 cutter must take the 6x4 / 256 px grid and handle several ink colours with edge decontamination (nearest-core-colour un-mix per pixel, so anti-aliased edges keep their true colour and get a smooth alpha, no dark halo). Then: write the 18 PNGs over `resources/icons/pages/` (keep file names; `_nav_page_icon` fits the glyph to `_NAV_ICON_PX` 20, opacities normal .85 / hover+checked 1 / disabled .32), re-run `scripts/make_screenshots.py`, look at the sidebar and header offscreen. Mockup first if the header badge is to change too.

## 4. Other ideas (not designed)

- Next / previous player in the player window; drag-and-drop to load a save; reopen the last save on start; keyboard shortcuts; CSV export of a list; saved filter sets.
- Staff window redesign (`StaffDetailDialog` is the old layout, no mockup).
- General Rating tab of the player window (needs in-game screens first); fill the Training tab.
- Asking price / transfer-listed status: needs the user's controlled experiment saves T0..T6 (see `HANDOVER.md` section 7).
- Packaging at 1.0: Flatpak (`io.github.acidtwin.FMBR24`) and a Windows .exe.
- README credit for the earlier Linux FM save-editing project (its name is a TODO comment in `README.md`, 'Inspired by').
- Sidebar nation flags and more list media (kit editor, `Small` club icons); see `HANDOVER.md` section 5 'List media', 'Not done'.
