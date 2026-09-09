# Uganda site network map

A geographically accurate replacement for the stylised Uganda locator graphic: real national
and district boundaries, real hydrology, and markers at each site's true coordinates.

Open `index.html` in a browser — it is a single self-contained file.

## What is in here

| Path | What it is |
| --- | --- |
| `index.html` | The finished, self-contained page (no build step, no runtime dependencies). |
| `data/sites.json` | The 15 sites — district, subregion, region, latitude, longitude. Edit this. |
| `data/uganda-geo.json` | Derived SVG path data for the country, its districts and its lakes. |
| `tools/fetch_geo.py` | Downloads Natural Earth vectors and regenerates `data/uganda-geo.json`. |
| `tools/build_map.py` | Renders `index.html` from the two data files plus `tools/template.html`. |
| `tools/template.html` | Page shell: design tokens, layout, tooltip behaviour. |

## Rebuilding

```sh
python3 tools/fetch_geo.py    # only needed once, or when the base map changes
python3 tools/build_map.py    # after any edit to data/sites.json or the template
```

`fetch_geo.py` caches the Natural Earth downloads in `.cache/` (gitignored, ~60 MB).
Neither script needs anything outside the standard library.

## How the map is built

* **Base map** — Natural Earth 10 m cultural and physical vectors (public domain): the Uganda
  boundary, Uganda's districts, and Lakes Victoria, Albert, Kyoga, Kwania, Edward and George.
  Lakes are clipped to the national outline so only Uganda's own waters are drawn.
* **Projection** — equirectangular with longitudes scaled by cos(1.4°N), the mid-latitude of the
  country. At full width one SVG point is about 0.617 km; the scale bar is derived from that
  number rather than drawn by eye.
* **Markers** — placed from the coordinates in `data/sites.json` through the same transform, so a
  marker cannot drift relative to the coastline. Labels are stacked in the side gutters by a
  collision pass, and leader lines are generated to match.
* **Greater Kampala** — Mpigi, Wakiso, Kampala (2 sites) and Mukono fall inside a 75 km box, too
  close to label individually at national scale, so the box is drawn on the national map and
  broken out at 2.6× in the inset.

## Known caveats

* Natural Earth carries Uganda's 112-district framework. **Kapelebyong** (split from Amuria in
  2018) and **Nabilatuk** (split from Nakapiripirit in 2018) postdate it, so those two markers sit
  at their true coordinates but inside their parent districts' outlines. Uganda now has 146
  districts; swapping in a current UBOS/OCHA district layer is the fix if that matters.
* Site coordinates are district headquarters towns, not individual facility addresses. Two of them
  (Kole, Iganga) sit within a few kilometres of a Natural Earth district line, so at very high zoom
  a marker can appear to fall on the neighbouring side of a boundary that is itself approximate.
