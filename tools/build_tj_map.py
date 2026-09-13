#!/usr/bin/env python3
"""Render tajikistan.html from data/tajikistan-geo.json + data/tj-sites.json."""
import json, os
from string import Template

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEO = json.load(open(os.path.join(ROOT, "data", "tajikistan-geo.json")))
RAW = json.load(open(os.path.join(ROOT, "data", "tj-sites.json")))
NAT, SITES = GEO["national"], GEO["sites"]
BY = {s["name"]: s for s in SITES}
UNMAPPED = RAW["unmapped"]

GUTTER = 270          # label column to the left of the map
LABEL_GAP = 54
# sites labelled in the left gutter, and the ones labelled in place out to the east
GUTTER_SITES = ["Panjakent", "Dushanbe", "Rudaki", "Khuroson", "Bokhtar", "J. Balkhi"]
INSIDE = {"Mastchoh": (424, 60), "Dehmoy": (424, 132), "Rasht": (470, 310),
          "Dangara": (408, 432), "Kulob": (424, 556)}
PIN = "M0 0c-5.5-8-10-13-10-18a10 10 0 1 1 20 0C10-13 5.5-8 0 0Z"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def n(v):
    return f"{v:,}"


def project(lon, lat, box):
    import math
    lon0, lat0, lon1, lat1 = box["bbox"]
    pad = (box["height"] - (lat1 - lat0) * box["ptPerDeg"]) / 2
    k = math.cos(math.radians((lat0 + lat1) / 2))
    return pad + (lon - lon0) * k * box["ptPerDeg"], pad + (lat1 - lat) * box["ptPerDeg"]


# --- stack the gutter labels so they never collide
slots = sorted(({"key": s["name"], "y": s["y"]} for s in (BY[k] for k in GUTTER_SITES)),
               key=lambda s: s["y"])
last = -1e9
for s in slots:
    s["ly"] = max(s["y"], last + LABEL_GAP)
    last = s["ly"]
LY = {s["key"]: s["ly"] for s in slots}


def badge(x, y, count, small=False):
    if count < 2:
        return ""
    r, dy = (5.2, -5.0) if small else (6.6, -23.6)
    cy = y - 7 if small else y - 26
    cls = " sm" if small else ""
    return (f'<circle class="badge-dot{cls}" cx="{x + (7 if small else 8.5):.1f}" cy="{cy:.1f}" r="{r}"/>'
            f'<text class="badge-num{cls}" x="{x + (7 if small else 8.5):.1f}" '
            f'y="{(y + dy) if small else (y - 23.6):.1f}">{count}</text>')


def pin(s, aria):
    return (f'<g class="pin" transform="translate({s["x"]:.1f} {s["y"]:.1f})">'
            f'<circle class="halo" cy="-18" r="15"/>'
            f'<path class="pin-body" d="{PIN}"/><circle class="pin-eye" cy="-18" r="3.7"/></g>'
            f'{badge(s["x"], s["y"], s["devices"])}')


def gutter_label(s):
    ly = LY[s["name"]]
    gx = -14
    leader = f'M{s["x"] - 10.5:.1f} {s["y"] - 18:.1f}L{gx + 34:.1f} {ly:.1f}L{gx:.1f} {ly:.1f}'
    sub = f'{n(s["screened"])} screened'
    if s["devices"] > 1:
        sub = f'{s["devices"]} devices &#183; {sub}'
    return f'''<g class="site" tabindex="0" role="listitem" data-site="{s['name']}"
     aria-label="{esc(s['name'])} — {esc(s['centre'])}, {n(s['screened'])} people screened">
  <path class="leader" d="{leader}"/>
  <text class="lbl" x="{gx - 8}" y="{ly - 3:.1f}" text-anchor="end">{esc(s['name'])}</text>
  <text class="sub" x="{gx - 8}" y="{ly + 18:.1f}" text-anchor="end">{sub}</text>
  {pin(s, s['name'])}
</g>'''


def inside_label(s):
    lx, ly = INSIDE[s["name"]]
    leader = f'M{s["x"] + 10.5:.1f} {s["y"] - 18:.1f}L{lx - 30:.1f} {ly - 9:.1f}L{lx - 10:.1f} {ly - 9:.1f}'
    return f'''<g class="site" tabindex="0" role="listitem" data-site="{s['name']}"
     aria-label="{esc(s['name'])} — {esc(s['centre'])}, {n(s['screened'])} people screened">
  <path class="leader" d="{leader}"/>
  <text class="lbl" x="{lx}" y="{ly - 3}">{esc(s['name'])}</text>
  <text class="sub" x="{lx}" y="{ly + 18}">{n(s['screened'])} screened</text>
  {pin(s, s['name'])}
</g>'''


km_bar = 100 / NAT["kmPerPt"]
lakes = "".join(f'<path class="lake" d="{l["d"]}"/>' for l in NAT["lakes"])
national = f'''<svg class="map-svg" viewBox="-{GUTTER} -42 {NAT["width"] + GUTTER:.0f} {NAT["height"] + 42:.0f}"
     role="list" aria-label="Map of Tajikistan showing centres operating portable X-ray devices">
  <defs><clipPath id="tj-clip"><path d="{NAT["country"]}"/></clipPath></defs>
  <path class="land" d="{NAT["country"]}"/>
  <g clip-path="url(#tj-clip)">
    <path class="site-district" d="{NAT["siteDistricts"]}"/>
    <path class="district" d="{NAT["districts"]}"/>
    <path class="region" d="{NAT["regions"]}"/>
    <path class="river" d="{NAT["rivers"]}"/>
    {lakes}
  </g>
  <path class="border" d="{NAT["country"]}"/>
  <g class="lake-names">
    <text x="356" y="152">Qayroqum Res.</text>
    <text x="600" y="640" transform="rotate(-8 600 640)">Panj</text>
    <text x="228" y="168">Syr&#8202;Darya</text>
  </g>
{"".join(gutter_label(BY[k]) for k in GUTTER_SITES)}
{"".join(inside_label(BY[k]) for k in INSIDE)}
  <g class="furniture">
    <g transform="translate(-210 52)">
      <path class="compass" d="M0-22 8 8 0 1-8 8Z"/><text class="compass-n" x="0" y="26">N</text>
    </g>
    <g transform="translate(752 676)">
      <rect class="bar" x="0" y="0" width="{km_bar / 2:.1f}" height="6"/>
      <rect class="bar alt" x="{km_bar / 2:.1f}" y="0" width="{km_bar / 2:.1f}" height="6"/>
      <text class="tick" x="0" y="24">0</text>
      <text class="tick" x="{km_bar / 2:.1f}" y="24" text-anchor="middle">50</text>
      <text class="tick" x="{km_bar:.1f}" y="24" text-anchor="middle">100&#8201;km</text>
    </g>
  </g>
</svg>'''

# --- footer panels
total = {k: sum(s[k] for s in SITES) + sum(u[k] for u in UNMAPPED)
         for k in ("devices", "screened", "presumptive", "detected", "confirmed")}
steps = [("People screened", total["screened"], None),
         ("Presumptive TB", total["presumptive"], "of those screened"),
         ("Cases detected", total["detected"], "of presumptive cases"),
         ("Bacteriologically confirmed", total["confirmed"], "of cases detected")]
prev = None
cascade = []
for label, value, of in steps:
    rate = "" if prev is None else f'<span class="rate">{value / prev * 100:.1f}%<em> {of}</em></span>'
    cascade.append(f'<div class="step"><span class="step-l">{label}</span>'
                   f'<span class="step-v">{n(value)}</span>{rate}</div>')
    prev = value

REGION_LABEL = {"Khatlon Region": "Khatlon", "Sughd Region": "Sughd", "Dushanbe": "Dushanbe",
                "Districts of Republican Subordination": "Districts of Republican Subordination"}
by_region = {}
for s in SITES:
    key = REGION_LABEL[s["region"]]
    by_region[key] = by_region.get(key, 0) + s["devices"]
by_region["Correctional institutions"] = sum(u["devices"] for u in UNMAPPED)
by_region["Gorno-Badakhshan"] = 0
rows = sorted(by_region.items(), key=lambda kv: -kv[1])
region_rows = "".join(
    f'<div class="reg{" zero" if v == 0 else ""}"><span class="reg-name">{k}</span>'
    f'<span class="reg-bar"><i style="width:{v / max(by_region.values()) * 100:.0f}%"></i></span>'
    f'<span class="reg-n">{v}</span></div>' for k, v in rows)

tip = {s["name"]: {"n": s["name"], "c": s["centre"], "r": REGION_LABEL[s["region"]],
                   "d": s["devices"], "s": n(s["screened"]), "p": n(s["presumptive"]),
                   "x": n(s["detected"]), "b": n(s["confirmed"]),
                   "g": f'{s["lat"]:.4f}°N, {s["lon"]:.4f}°E',
                   "a": "district interior point" if s["anchor"] == "district" else "city"}
       for s in SITES}

html = Template(open(os.path.join(ROOT, "tools", "template_tj.html")).read()).substitute(
    map=national, cascade="".join(cascade), region_rows=region_rows,
    tip_data=json.dumps(tip, separators=(",", ":")),
    devices=total["devices"], centres=sum(len(s["no"].split(",")) for s in SITES) + len(UNMAPPED),
    screened=n(total["screened"]), confirmed=n(total["confirmed"]),
    unmapped_devices=sum(u["devices"] for u in UNMAPPED),
    unmapped_screened=n(sum(u["screened"] for u in UNMAPPED)))
out = os.path.join(ROOT, "tajikistan.html")
open(out, "w").write(html)
print(f"wrote {out} ({os.path.getsize(out) / 1024:.0f} KB)")
print("gutter label slots:", {k: round(v) for k, v in LY.items()})
