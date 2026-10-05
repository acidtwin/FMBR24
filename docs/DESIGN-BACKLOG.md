# Design backlog: mockups to come back to

Designed surfaces that are not (fully) built or decided yet. Rule: a mockup is approved by the user BEFORE any app code (`CLAUDE.md`, mockup first; translate mechanically, never by eye). Open the mockups straight from disk in the user's own Chrome (`xdg-open file://<repo>/mockups/<name>.html`; the Claude browser pane shows file:// pages as a static snapshot, scripts do not run); NO web server. State of the app: `HANDOVER.md`.

## 1. Compare players

- **Status:** BUILT and merged to `main`: sidebar page 'Compare Players' (`gui/compare_page.py`), pickers (`gui/player_picker.py`), `Compare to...` popup in the player window, Detailed radar (`fm_editor/radar_axes.py`), recents (`fm_editor/recents.py`). Plan and decisions: `docs/plans/compare-players.md` (marked BUILT). Everything below is the ORIGINAL design: the window / picker-dialog flow, the 'Compare with...' button name and the list-row launch were superseded (no Compare from list rows for now; a context-menu entry is cheap if wanted).
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

- **Status:** BUILT. The user chose A (Diamond) as the DEFAULT; B Square-knot, C Perspective, D Honeycomb (light sweep + goal post) and the old Pitch lines stay as options in Settings > Header texture (`header_texture`, `gui/header_net.py`, test `tests/test_header_texture.py`). Nothing left here except tuning if the user asks.
- **Mockup:** `mockups/header-net.html`; `?v=a|b|c|d` (`g` = the current pitch grid, reference), `&glow` (animate the loading glow), `&glow=peak`, `&bare=1`, `&k=` strength, `&w=` header width. The file header comment holds the generator pseudocode and constants.
- **Variants:** A diamond mesh (classic netting); B square-knot net (sagging orthogonal mesh; the previous agent's RECOMMENDATION); C perspective net hanging in the goal mouth (radial mask + corner shadow); D honeycomb + light sweep + post/crossbar corner.
- **Build notes (as built):** see HANDOVER hero section. Deviations from the mockup: flat caps / bevel joins (speed), curved nets stroked per strand (opaque union, then alpha), glow halo/core built from the same strands and mask.

## 3. Sidebar solid icon set

- **Status:** waiting for the user to generate the icon sheet. Not built. The header badge and sidebar keep the CURRENT line icons (`resources/icons/pages/*.png`, 18 files) meanwhile.
- **Wanted:** new solid-style (filled) icons for the sidebar. Palette: purple `#6933BD`, highlight `#735CE4`, off-white `#ECEAF2`, green `#4caf82` spark; pentagon motif.
- **Image prompt** (already given to the user): ONE 18-icon sheet, 6 columns x 4 rows of 256 px cells on a flat `#14151A` background, 1536x1024 image.
- **What the build needs:** `scripts/cut_icon_sheet.py` today cuts a 3x2 sheet of 512 px cells with TWO ink colours (off-white or purple) by colour un-mix. A v2 cutter must take the 6x4 / 256 px grid and handle several ink colours with edge decontamination (nearest-core-colour un-mix per pixel, so anti-aliased edges keep their true colour and get a smooth alpha, no dark halo). Then: write the 18 PNGs over `resources/icons/pages/` (keep file names; `_nav_page_icon` fits the glyph to `_NAV_ICON_PX` 20, opacities normal .85 / hover+checked 1 / disabled .32), re-run `scripts/make_screenshots.py`, look at the sidebar and header offscreen. Mockup first if the header badge is to change too.

## 4. Reserved Dev/ability graphic E: growth stairs

Designed in `mockups/player-lists.html` (`?dev=e`), NOT used now (the Dev column uses style B five pips, the Best by Role Rating uses style D ring). Keep for a future use.
Paint recipe (QPainter, antialiasing on, no pixmaps): 5 ascending bars, width 3, gap 1.5 (5*3 + 4*1.5 = 21 wide), heights 5, 7.5, 10, 12.5, 15, bottom aligned at cy+7.5
(cy = cell.top + h/2, x = cell.left + 10), corner radius 0.8. Bar i is lit when `i < ceil(v/4)` (v = 1-20), lit colour = tier(v) (red <=4, orange <=8, grey <=11, white <=13, yellow <=16, green),
unlit #3A4050. Reads as a rising curve in greyscale. Tooltip 'Dev 14 of 20', sort by the raw value. Styles A (slim meter), C (chevrons) are also kept in the mockup as alternatives.

## 5. Other ideas (not designed)

- Next / previous player in the player window; drag-and-drop to load a save; reopen the last save on start; keyboard shortcuts; CSV export of a list; saved filter sets.
- Staff window redesign (`StaffDetailDialog` is the old layout, no mockup).
- General Rating tab of the player window (still a 'coming soon' placeholder; the user said just rename Role Rating, so this stays open). Reference the user showed (FM Genie Scout's General Rating screen): a list of GENERIC role categories (Goalkeeper, Sweeper, Centre Back, Full Back, Wing Back, Defensive Midfielder, Midfielder, Attacking Midfielder, Winger, Fast Striker, Target Striker), each with a percentage, plus coloured dots on a pitch. Build only after the user asks (mockup first). Also fill the Training tab beyond Recommended traits.
- Contract & Transfer page rows like FM Genie Scout's Transfer screen: Type, Value, Sale Value (not in the save), Wage, Started, Expires, Availability, Squad Status, Perceived Squad Status, Interested (clubs; not found in the save). Waiting for the user's Spurs squad Contract-view screenshot (Squad Status + Contract Type columns) to decode both (candidate record `0x04 0x43`, nibbles).
- Asking price / transfer-listed status: needs the user's controlled experiment saves T0..T6 (see `HANDOVER.md` section 7).
- Packaging at 1.0: Flatpak (`io.github.acidtwin.FMBR24`) and a Windows .exe.
- README credit for the earlier Linux FM save-editing project (its name is a TODO comment in `README.md`, 'Inspired by').
- Sidebar nation flags and more list media (kit editor, `Small` club icons); see `HANDOVER.md` section 5 'List media', 'Not done'.

## Info tags the game has that we cannot read yet

The built Info column (`fm_editor/infotags.py`) shows only tags derivable from parsed data. Missing FM tags, each a future add once its data is found: Spt / Ask / Wnt / Slt (transfer-listed, asking price, wanted, shortlisted: needs the transfer-status experiment saves T0..T6, HANDOVER section 7), Unh (unhappy: morale / promise data), Amg / PR (agent / pre-contract: contract negotiation records), others. To add one: code in `PRI`, width/colours in `TW` / `ST` (gui/info_column.py), a rule in `tags_for`.
