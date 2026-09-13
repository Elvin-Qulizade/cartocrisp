# cartocrisp

Generate a crisp, infinitely-zoomable **vector** map snapshot (SVG or PDF) from a map link — street names and details stay sharp at any zoom level, because the output is real vector data, not a raster screenshot.

## Why

Standard map screenshots blur when you zoom in. cartocrisp pulls OpenStreetMap vector data for the area your link points to and renders it directly to SVG/PDF, so the result never pixelates.

## Usage

No pre-installed Python required — the launcher scripts bootstrap everything via [uv](https://github.com/astral-sh/uv).

```bash
# macOS / Linux
./cartocrisp.sh "https://www.google.com/maps/@40.4093,49.8671,16z" -o baku.svg

# Windows
./cartocrisp.ps1 "https://www.google.com/maps/@40.4093,49.8671,16z" -o baku.svg
```

Options:
- `-o, --output` — output file path (`.svg` or `.pdf`)
- `--width`, `--height` — canvas size in pixels (default 1600x1200)
- `--lang` — `az`, `en`, `tr`, or `ru` (default: your OS locale, falling back to English)

Supported link formats: Google Maps URLs (including shortened `maps.app.goo.gl` links), OpenStreetMap URLs, or a plain `lat,lon,zoom` string.

**Note on speed:** cartocrisp fetches live data from the free, shared Overpass API. For a dense city center at street-level zoom, a request can legitimately take 30-90 seconds, and occasionally longer under heavy public load — this is normal, not a hang. If a request fails with "Could not reach OpenStreetMap data servers," it's almost always the shared public API being slow or rate-limiting, not a bug — wait a bit and retry, try a smaller `--width`/`--height`, or self-host Overpass for reliable/heavy use (see below).

### Web UI

```bash
./cartocrisp.sh web
```

Opens a local page at `http://127.0.0.1:8765` where you can paste a link and download the result.

## Data & Licensing

Map data comes from [OpenStreetMap](https://www.openstreetmap.org) via the public Overpass API and is licensed under the [ODbL](https://opendatacommons.org/licenses/odbl/) — every generated file includes the required "© OpenStreetMap contributors" attribution.

The public Overpass API has fair-use limits. For heavy use, run your own Overpass instance and pass its URL(s) to `OverpassClient(mirrors=[...])` (see `src/cartocrisp/overpass.py`).

This project is MIT licensed.
