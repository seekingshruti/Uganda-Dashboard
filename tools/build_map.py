#!/usr/bin/env python3
"""Render index.html from data/uganda-geo.json + data/sites.json."""
import json, math, os
from string import Template

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEO = json.load(open(os.path.join(ROOT, "data", "uganda-geo.json")))
SITES = json.load(open(os.path.join(ROOT, "data", "sites.json")))["sites"]

NAT, INS = GEO["national"], GEO["inset"]
GUTTER = 260          # label column either side of the national map
LABEL_GAP = 64        # minimum vertical spacing between stacked labels (name + subregion)
SIDE = {"Adjumani": -1, "Oyam": -1, "Hoima": -1, "Ntoroko": -1,
        "Abim": 1, "Kole": 1, "Nabilatuk": 1, "Kapelebyong": 1, "Serere": 1, "Iganga": 1}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def project(lon, lat, box):
    """Same equirectangular transform fetch_geo.py used, recovered from the stored bbox."""
    lon0, lat0, lon1, lat1 = box["bbox"]
    pad = (box["height"] - (lat1 - lat0) * box["ptPerDeg"]) / 2
    k = math.cos(math.radians((lat0 + lat1) / 2))
    return pad + (lon - lon0) * k * box["ptPerDeg"], pad + (lat1 - lat) * box["ptPerDeg"]


def coord_label(lat, lon):
    return f"{abs(lat):.4f}°{'N' if lat >= 0 else 'S'}, {abs(lon):.4f}°E"


# ---------------------------------------------------------------- national map
metro = [s for s in SITES if s["region"] == "Central"]
outer = [s for s in SITES if s["region"] != "Central"]
for s in SITES:
    s["x"], s["y"] = project(s["lon"], s["lat"], NAT)
    s["ix"], s["iy"] = project(s["lon"], s["lat"], INS)
    s["id"] = s["name"].lower()

# stack the gutter labels so they never collide
placed = {}
for side in (-1, 1):
    col = sorted([s for s in outer if SIDE[s["name"]] == side], key=lambda s: s["y"])
    last = -1e9
    for s in col:
        y = max(s["y"], last + LABEL_GAP)
        placed[s["name"]] = y
        last = y

lon0, lat0, lon1, lat1 = INS["bbox"]
bx0, by0 = project(lon0, lat1, NAT)
bx1, by1 = project(lon1, lat0, NAT)
eq_y = project(32.0, 0.0, NAT)[1]

PIN = ("M0 0c-7.2-10.4-13-17-13-23.5a13 13 0 1 1 26 0C13-17 7.2-10.4 0 0Z")


def gutter_site(s):
    d = SIDE[s["name"]]
    ly = placed[s["name"]]
    gx = (-14 if d < 0 else NAT["width"] + 14)
    ex = gx + d * 34            # elbow
    anchor = "end" if d < 0 else "start"
    head_y = s["y"] - 23.5
    leader = (f'M{s["x"] + d * 13.5:.1f} {head_y:.1f}L{ex:.1f} {ly:.1f}L{gx:.1f} {ly:.1f}')
    badge = ""
    if s["count"] > 1:
        badge = (f'<circle class="badge-dot" cx="{s["x"] + 11:.1f}" cy="{s["y"] - 34:.1f}" r="8.6"/>'
                 f'<text class="badge-num" x="{s["x"] + 11:.1f}" y="{s["y"] - 30.6:.1f}">{s["count"]}</text>')
    return f'''<g class="site" tabindex="0" role="listitem" data-site="{s['id']}"
     aria-label="{esc(s['name'])} — {esc(s['district'])} District, {esc(s['region'])} Region">
  <path class="leader" d="{leader}"/>
  <text class="lbl" x="{gx + d * 8:.1f}" y="{ly - 3:.1f}" text-anchor="{anchor}">{esc(s['name'])}</text>
  <text class="sub" x="{gx + d * 8:.1f}" y="{ly + 18:.1f}" text-anchor="{anchor}">{esc(s['subregion'])}</text>
  <g class="pin" transform="translate({s['x']:.1f} {s['y']:.1f})">
    <circle class="halo" cy="-23.5" r="20"/>
    <path class="pin-body" d="{PIN}"/><circle class="pin-eye" cy="-23.5" r="4.8"/>
  </g>{badge}
</g>'''


def metro_dot(s):
    badge = ""
    if s["count"] > 1:
        badge = (f'<circle class="badge-dot sm" cx="{s["x"] + 9:.1f}" cy="{s["y"] - 9:.1f}" r="6.6"/>'
                 f'<text class="badge-num sm" x="{s["x"] + 9:.1f}" y="{s["y"] - 6.4:.1f}">{s["count"]}</text>')
    # the same four sites are listed accessibly in the inset, so keep these out of the a11y tree
    return (f'<g class="site dot" data-site="{s["id"]}" aria-hidden="true">'
            f'<circle class="halo" cx="{s["x"]:.1f}" cy="{s["y"]:.1f}" r="15"/>'
            f'<circle class="dot-mark" cx="{s["x"]:.1f}" cy="{s["y"]:.1f}" r="6.4"/>{badge}</g>')


km_bar = 100 / NAT["kmPerPt"]
national_sites = "\n".join(gutter_site(s) for s in outer)
metro_dots = "".join(metro_dot(s) for s in metro)
lakes_nat = "".join(f'<path class="lake" d="{l["d"]}"/>' for l in NAT["lakes"])

# leader from the metro box out to its gutter label
mb_y = max(placed.values()) + 100
national_map = f'''<svg class="map-svg" viewBox="-{GUTTER} 0 {NAT["width"] + 2 * GUTTER:.0f} {NAT["height"]:.0f}"
     role="list" aria-label="Map of Uganda showing 15 program sites">
  <defs>
    <clipPath id="ug-clip"><path d="{NAT["country"]}"/></clipPath>
  </defs>
  <path class="land" d="{NAT["country"]}"/>
  <g clip-path="url(#ug-clip)">
    <path class="district" d="{NAT["districts"]}"/>
    {lakes_nat}
  </g>
  <path class="border" d="{NAT["country"]}"/>
  <g class="equator">
    <line x1="-6" y1="{eq_y:.1f}" x2="{bx0:.1f}" y2="{eq_y:.1f}"/>
    <line x1="{bx1:.1f}" y1="{eq_y:.1f}" x2="{NAT["width"]:.0f}" y2="{eq_y:.1f}"/>
    <text x="-14" y="{eq_y + 5:.1f}" text-anchor="end">EQUATOR&#8201;&#183;&#8201;0&#176;</text>
  </g>
  <g class="lake-names">
    <text x="250" y="475" transform="rotate(-62 250 475)">L.&#8202;Albert</text>
    <text x="643" y="507">Lake&#8202;Kyoga</text>
    <text x="700" y="884">Lake&#8202;Victoria</text>
  </g>
  <g class="detail-box">
    <rect x="{bx0:.1f}" y="{by0:.1f}" width="{bx1 - bx0:.1f}" height="{by1 - by0:.1f}" rx="4"/>
    <path class="leader" d="M{bx1:.1f} {(by0 + by1) / 2:.1f}L{NAT["width"] - 20:.0f} {mb_y:.1f}L{NAT["width"] + 14:.0f} {mb_y:.1f}"/>
    <text class="lbl" x="{NAT["width"] + 22:.0f}" y="{mb_y - 3:.1f}">Greater Kampala</text>
    <text class="sub" x="{NAT["width"] + 22:.0f}" y="{mb_y + 18:.1f}">5 sites &#183; see detail</text>
  </g>
  {metro_dots}
{national_sites}
  <g class="furniture">
    <g transform="translate(946 44)">
      <path class="compass" d="M0-22 8 8 0 1-8 8Z"/>
      <text class="compass-n" x="0" y="26">N</text>
    </g>
    <g transform="translate(300 1006)">
      <rect class="bar" x="0" y="0" width="{km_bar / 2:.1f}" height="6"/>
      <rect class="bar alt" x="{km_bar / 2:.1f}" y="0" width="{km_bar / 2:.1f}" height="6"/>
      <text class="tick" x="0" y="24">0</text>
      <text class="tick" x="{km_bar / 2:.1f}" y="24" text-anchor="middle">50</text>
      <text class="tick" x="{km_bar:.1f}" y="24" text-anchor="middle">100&#8201;km</text>
    </g>
  </g>
</svg>'''

# ------------------------------------------------------------------- the inset
INS_LBL = {"Wakiso": (13, 3, "start"), "Kampala": (-13, 3, "end"),
           "Mukono": (0, -15, "middle"), "Mpigi": (13, 3, "start")}
inset_marks = []
for s in metro:
    dx, dy, anchor = INS_LBL[s["name"]]
    name = f'{s["name"]}&#8202;&#215;2' if s["count"] > 1 else s["name"]
    badge = ""  # in the inset the count rides in the label instead
    inset_marks.append(
        f'<g class="site" tabindex="0" role="listitem" data-site="{s["id"]}" '
        f'aria-label="{esc(s["name"])} — {esc(s["district"])} District">'
        f'<circle class="halo" cx="{s["ix"]:.1f}" cy="{s["iy"]:.1f}" r="13"/>'
        f'<circle class="dot-mark" cx="{s["ix"]:.1f}" cy="{s["iy"]:.1f}" r="6.2"/>{badge}'
        f'<text class="ins-lbl" x="{s["ix"] + dx:.1f}" y="{s["iy"] + dy:.1f}" '
        f'text-anchor="{anchor}">{name}</text></g>')

ins_km = 20 / INS["kmPerPt"]
inset_lakes = "".join(f'<path class="lake" d="{l["d"]}"/>' for l in INS["lakes"])
inset_svg = f'''<svg class="inset-svg" viewBox="0 0 {INS["width"]:.0f} {INS["height"]:.0f}"
     role="list" aria-label="Greater Kampala detail map">
  <defs>
    <clipPath id="ins-clip"><rect x="0" y="0" width="{INS["width"]:.0f}" height="{INS["height"]:.0f}" rx="6"/></clipPath>
  </defs>
  <g clip-path="url(#ins-clip)">
    <rect class="ins-bg" x="0" y="0" width="{INS["width"]:.0f}" height="{INS["height"]:.0f}"/>
    <path class="land" d="{INS["country"]}"/>
    <path class="district" d="{INS["districts"]}"/>
    {inset_lakes}
    <text class="ins-water" x="196" y="196">Lake Victoria</text>
    {"".join(inset_marks)}
    <g class="furniture" transform="translate(14 {INS["height"] - 16:.0f})">
      <rect class="bar" x="0" y="0" width="{ins_km:.1f}" height="4"/>
      <text class="tick" x="{ins_km + 7:.1f}" y="5">20&#8201;km</text>
    </g>
  </g>
  <rect class="ins-frame" x="0.5" y="0.5" width="{INS["width"] - 1:.0f}" height="{INS["height"] - 1:.0f}" rx="6"/>
</svg>'''

# --------------------------------------------------------------- stats + notes
lat_span = (max(s["lat"] for s in SITES) - min(s["lat"] for s in SITES)) * 111.32
lon_span = (max(s["lon"] for s in SITES) - min(s["lon"] for s in SITES)) * 111.32 * 0.9998
regions = {}
for s in SITES:
    regions[s["region"]] = regions.get(s["region"], 0) + s["count"]
region_rows = "".join(
    f'<div class="reg"><span class="reg-name">{k}</span>'
    f'<span class="reg-bar"><i style="width:{v / 15 * 100:.0f}%"></i></span>'
    f'<span class="reg-n">{v}</span></div>'
    for k, v in sorted(regions.items(), key=lambda kv: -kv[1]))

tip_data = json.dumps({s["id"]: {"n": s["name"], "d": s["district"], "s": s["subregion"],
                                 "r": s["region"], "c": coord_label(s["lat"], s["lon"]),
                                 "k": s["count"]} for s in SITES}, separators=(",", ":"))

TPL = Template(open(os.path.join(ROOT, "tools", "template.html")).read())
html = TPL.substitute(
    national_map=national_map, inset=inset_svg, region_rows=region_rows,
    tip_data=tip_data, n_sites=sum(s["count"] for s in SITES), n_districts=len(SITES),
    n_regions=len(regions), lat_span=f"{lat_span:,.0f}", lon_span=f"{lon_span:,.0f}",
    km_per_pt=f"{NAT['kmPerPt']:.3f}", ins_zoom=f"{NAT['kmPerPt'] / INS['kmPerPt']:.1f}")
out = os.path.join(ROOT, "index.html")
open(out, "w").write(html)
print(f"wrote {out} ({os.path.getsize(out) / 1024:.0f} KB)")
