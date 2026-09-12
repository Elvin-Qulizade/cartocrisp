# cartocrisp — Design Spec

## Problem

Standard map screenshots are raster: zoom in and they blur, street names become unreadable. A friend's workaround was a script that split a Google Maps view into a 9-cell grid, zoomed and screenshotted each cell separately, then stitched them back together — trading screenshot resolution for coverage, but still fundamentally raster.

cartocrisp solves this properly: given a map link, produce a **true vector** (SVG/PDF) snapshot of that area — infinitely zoomable, street names rendered as real text, no native/GIS toolchain required to install or run.

## Scope (MVP)

- Input: a Google Maps URL, an OSM URL, or a plain `lat,lon,zoom` string.
- Output: an SVG (and optionally PDF) file showing roads (with names), buildings, water, parks/greenery, and place labels for the area implied by the input.
- Interfaces: CLI and a local web UI, both built on one shared core library.
- Runs with zero manual setup, even on a machine with no Python installed.
- UI/CLI text available in Azerbaijani, English, Turkish, Russian.

Out of scope for MVP: routes/directions rendering, custom color themes, non-OSM data sources, printing/paper-size layout tools.

## Architecture

```
link → [link_parser] → (lat, lon, zoom)
                              ↓
                     [bbox_calculator] → bounding box (degrees)
                              ↓
                     [overpass_client] → raw OSM elements (local cache)
                              ↓
                    [geometry_builder] → typed geometry layers
                              ↓
                        [svg_renderer] → SVG (+ optional PDF) file
                              ↓
                    [cli] and [web] → deliver file to user
```

All five pipeline stages live in `cartocrisp/core/` as a plain Python library with no I/O side effects beyond the Overpass HTTP call and the cache, so `cli` and `web` are thin wrappers that call the same `generate(link, options) -> Path` function.

### Components

- **link_parser** — recognizes Google Maps URLs (`@lat,lon,zoomz`, `!3d..!4d..` variants, short `goo.gl/maps` links resolved via HTTP redirect), OSM URLs (`#map=zoom/lat/lon`), and a raw `lat,lon,zoom` string. Raises a typed `UnrecognizedLinkError` with the supported formats listed, translated per active locale.
- **bbox_calculator** — converts center + zoom + requested canvas size into a geographic bounding box, using the standard Web Mercator zoom→meters-per-pixel formula. Enforces a maximum area (configurable) to keep Overpass queries bounded.
- **overpass_client** — queries the Overpass API for ways/relations/nodes tagged as roads, buildings, water, landuse=park/forest/grass, and named places within the bbox. Caches raw responses keyed by rounded bbox+zoom in a local SQLite file (`~/.cache/cartocrisp/`) so repeat runs on the same area don't re-hit the network. Rotates through a small list of public Overpass mirrors on timeout/rate-limit with exponential backoff.
- **geometry_builder** — turns Overpass elements into typed, projected geometry layers (`roads`, `buildings`, `water`, `greenery`, `labels`), each a list of projected point sequences (or a point + text for labels) in SVG user-space coordinates.
- **svg_renderer** — pure-Python renderer (no native dependencies). Draws layers bottom-to-top (water/greenery → buildings → roads → labels) with per-road-type stroke width/color, building/water/park fills, and text elements for street and place names with basic overlap avoidance (skip a label if its bounding box collides with an already-placed one). Writes an `© OpenStreetMap contributors` attribution text element into every output. PDF export reuses the same drawing calls via a second lightweight backend.
- **i18n** — a small key→string lookup (`cartocrisp/i18n/{az,en,tr,ru}.json`), locale chosen from `--lang` / `Accept-Language` header / OS locale, defaulting to English if unavailable. A test asserts all four locale files have identical key sets.
- **cli** — `cartocrisp <link> -o output.svg [--width] [--height] [--format svg|pdf] [--lang az|en|tr|ru]`.
- **web** — a minimal FastAPI + vanilla-JS single page: paste a link, click generate, preview the SVG inline, download it. Same-origin only, no accounts, no persistence beyond the Overpass cache.

### Zero-setup execution

Because the renderer is pure Python (no Mapnik/GDAL/native libs — this was originally planned around Mapnik but that requires a system-installed native library, which conflicts with "must run with no pre-existing Python/setup"), every dependency is a pure-Python or manylinux-wheel package (`httpx`, `fastapi`, `uvicorn`). This makes it possible to bootstrap fully via [uv](https://github.com/astral-sh/uv), which itself ships as a single static binary requiring no pre-installed Python:

- `cartocrisp.sh` (macOS/Linux) and `cartocrisp.ps1` (Windows) launcher scripts:
  1. Check for `uv` on PATH; if absent, download the official uv install script/binary into `~/.local/bin` (or `%LOCALAPPDATA%`) — a one-time, no-Python-required step.
  2. Run `uv run --python 3.12 -m cartocrisp <args>` — uv transparently downloads an isolated Python 3.12 if needed and creates/reuses a managed venv with the project's locked dependencies.
  3. For the web UI, the launcher runs `uv run -m cartocrisp.web` and opens the default browser at `http://127.0.0.1:8765`.
- End users on any OS can clone the repo (or download a release zip) and run one launcher script with no prior Python or venv setup of their own.

## Data flow example

1. User runs `./cartocrisp.sh "https://maps.google.com/@40.409,49.867,16z" -o baku.svg --lang az`.
2. `link_parser` extracts `(40.409, 49.867, 16)`.
3. `bbox_calculator` computes a bbox sized for the default 1600×1200 canvas at zoom 16.
4. `overpass_client` checks the local cache; on miss, queries Overpass, caches the result.
5. `geometry_builder` converts elements into projected layers.
6. `svg_renderer` draws layers + attribution, writes `baku.svg`.
7. CLI prints a localized success message with the output path.

## Error handling

- Unrecognized link → `UnrecognizedLinkError` with example formats, localized.
- Overpass timeout/rate-limit → retry with backoff, then rotate to the next mirror; if all mirrors fail, a clear localized error naming the last failure.
- bbox exceeds the configured max area → localized error suggesting a higher zoom level.
- Area with little/no OSM data (ocean, desert) → still renders (background + attribution only) plus a localized warning, not an error.
- Web UI surfaces the same error messages as the CLI, as JSON + a rendered message in the page.

## Testing

- Unit tests: `link_parser` against a table of real-world Google Maps/OSM URL variants and malformed inputs; `bbox_calculator` math against known reference values.
- Integration test: a recorded/fixture Overpass response run through `geometry_builder` → `svg_renderer`, asserting expected element counts (e.g., N road paths, M labels) in the output SVG — no live network call, deterministic.
- i18n test: all locale JSON files have identical key sets; CLI `--help` renders without missing-key errors in each locale.
- Manual smoke test (done once implementation lands): run the launcher against a real, recognizable location and visually confirm the SVG.

## Licensing

- Project code: MIT license.
- Rendered output always includes an `© OpenStreetMap contributors` attribution element (ODbL requirement).
- README documents Overpass API fair-use limits and how to point the tool at a self-hosted Overpass instance for heavy use.
