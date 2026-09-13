# Programme site maps

Geographically accurate locator maps built from real boundary data — national, region and
district outlines, real hydrology, and markers placed by coordinate rather than by eye.

| Map | Page | Image |
| --- | --- | --- |
| Uganda site network | `index.html` | `uganda-site-map.png` |
| Tajikistan portable X-ray devices, 2025 | `tajikistan.html` | `tajikistan-xray-map.png` |

Each map is a single self-contained HTML file with no runtime dependencies, generated from a
data file plus a template. The two share a palette and type system but not code — the Uganda
and Tajikistan pipelines are deliberately separate so a change to one cannot break the other.

## Uganda site network

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


## Tajikistan portable X-ray devices

Built from the 2025 report on portable X-ray activity — 15 devices across 13 reporting centres —
plus one mobile CXR workflow added on top of that table.

| Path | What it is |
| --- | --- |
| `tajikistan.html` | The finished page. |
| `data/tj-sites.json` | The reporting centres and their five reported columns. Edit this. |
| `data/tajikistan-geo.json` | Derived paths for the country, regions, districts, rivers and the site anchor points. |
| `tools/fetch_geo_tj.py` | Downloads boundaries and hydrology, computes the anchors, writes the geo file. |
| `tools/build_tj_map.py` | Renders `tajikistan.html`. |
| `tools/template_tj.html` | Page shell for the Tajikistan plate. |

```sh
python3 tools/fetch_geo_tj.py
python3 tools/build_tj_map.py
```

### How the sites are placed

* **Boundaries** — geoBoundaries gbOpen ADM0/ADM1/ADM2 (CC BY 4.0), fetched through GitHub's LFS
  media endpoint. Rivers (Syr Darya, Zarafshon, Panj, Amu Darya, Pamir) and the Qayroqum
  reservoir come from Natural Earth 10 m.
* **Anchors** — Dushanbe, Bokhtar, Kulob and Panjakent sit at their city coordinates. The
  district-named centres sit at the *pole of inaccessibility* of their district: the interior
  point furthest from the district's own boundary, computed by grid search in `fetch_geo_tj.py`.
  That keeps a marker unambiguously inside the district it belongs to. The markers say which
  district a device serves; they are not facility addresses.
* **Districts hosting a device are shaded**, so coverage reads from the fill as well as the pins.
* **The Dushanbe pair** — Dushanbe city (2 devices, report rows 1 and 2) and Rudaki sit ~12 km
  apart, so their markers overlap slightly at national scale. They are drawn as two separate
  markers with a paper casing and their own labels rather than an inset, so the whole network
  reads in a single view that can be screenshotted as one image.

### Known caveats

* **Correctional institutions (2 devices, 9,999 screened) are counted but not mapped** — they
  are deployed across the prison system rather than at one location.
* **The extra mobile workflow is not in the report table.** The plate carries no partner
  attribution — naming the funder of one unit would oblige naming the funders of the other 15 —
  so `programme` is held in `data/tj-sites.json` for reference but never rendered. It is 1 mobile CXR unit
  coordinated from Dushanbe, rotating across Muminobod, Ayni, Istaravshan and Konibodom (the
  boundary data's spellings of Muminabad and Kanibadam), targeting Afghan-immigrant active case
  finding and mobile/high-risk populations. It counts toward the 16-device total and toward
  Dushanbe in the regional breakdown, but reports no screening figures, so every count in the
  cascade covers the 15 reported devices only. Its districts are drawn hatched with ring markers
  rather than shaded with pins, because the unit covers them on rotation rather than sitting in one.
* Jaloliddin Balkhi district appears in the boundary data under its former name, **Rumi**.
* Dehmoy is anchored to **Ghafurov district**, which contains the village; Rasht and Mastchoh
  anchors sit 10-25 km from their district centre towns, which is the cost of the interior-point
  method on large mountain districts.
* All five reported columns (devices, screened, presumptive, detected, confirmed) were summed and
  reconcile exactly to the report's own totals; `tools/build_tj_map.py` recomputes them at build
  time rather than hard-coding them.
