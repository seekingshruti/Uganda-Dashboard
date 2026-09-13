#!/usr/bin/env python3
"""Build data/tajikistan-geo.json: SVG path data for Tajikistan plus the site anchor points.

Boundaries: geoBoundaries gbOpen (ADM0/ADM1/ADM2, CC-BY 4.0).
Rivers and reservoirs: Natural Earth 10m physical vectors (public domain).
Run from the repo root:  python3 tools/fetch_geo_tj.py
"""
import json, math, os, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, ".cache")
GB = "https://media.githubusercontent.com/media/wmgeolab/geoBoundaries/main/releaseData/gbOpen/TJK"
NE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson"
RIVERS = ("Syr  Darya", "Panj", "Amu  Darya", "Zarafshon", "Pamir", "Naryn")
LAKES = ("Obanbori Qayroqum",)

NAT_W, NAT_PAD = 1000.0, 8.0


def fetch(name, url):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, name)
    if not os.path.exists(path):
        print("downloading", name)
        urllib.request.urlretrieve(url, path)
    with open(path) as fh:
        return json.load(fh)


def polys(geom):
    return [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]


def lines(geom):
    return [geom["coordinates"]] if geom["type"] == "LineString" else geom["coordinates"]


def bbox_of(geom):
    pts = ([c for p in polys(geom) for c in p[0]] if geom["type"].endswith("Polygon")
           else [c for l in lines(geom) for c in l])
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def make_projection(lon0, lat0, lon1, lat1, width, pad):
    k = math.cos(math.radians((lat0 + lat1) / 2))
    scale = (width - 2 * pad) / ((lon1 - lon0) * k)
    height = (lat1 - lat0) * scale + 2 * pad

    def project(lon, lat):
        return pad + (lon - lon0) * k * scale, pad + (lat1 - lat) * scale

    return project, scale, height


def ring_path(pts, tol):
    keep = [pts[0]]
    for p in pts[1:]:
        if abs(p[0] - keep[-1][0]) + abs(p[1] - keep[-1][1]) > tol:
            keep.append(p)
    return keep


def to_path(geom, project, min_area=0.0, tol=0.4):
    out = []
    for poly in polys(geom):
        for ring in poly:
            keep = ring_path([project(x, y) for x, y in ring], tol)
            if len(keep) < 4:
                continue
            area = abs(sum(keep[i][0] * keep[i - 1][1] - keep[i - 1][0] * keep[i][1]
                           for i in range(len(keep)))) / 2
            if area < min_area:
                continue
            out.append("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in keep) + "Z")
    return "".join(out)


def to_line_path(geom, project, tol=0.5):
    out = []
    for line in lines(geom):
        keep = ring_path([project(x, y) for x, y in line], tol)
        if len(keep) > 1:
            out.append("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in keep))
    return "".join(out)


def inside(lon, lat, geom):
    hit = False
    for poly in polys(geom):
        for i, ring in enumerate(poly):
            c, n = False, len(ring)
            for a in range(n):
                x1, y1 = ring[a]
                x2, y2 = ring[(a + 1) % n]
                if (y1 > lat) != (y2 > lat) and lon < (x2 - x1) * (lat - y1) / (y2 - y1) + x1:
                    c = not c
            if i == 0 and c:
                hit = True
            elif i and c:
                hit = False
    return hit


def seg_distance(lon, lat, geom):
    best = 1e9
    for poly in polys(geom):
        for ring in poly:
            for a in range(len(ring)):
                x1, y1 = ring[a]
                x2, y2 = ring[(a + 1) % len(ring)]
                dx, dy = x2 - x1, y2 - y1
                t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, ((lon - x1) * dx + (lat - y1) * dy) / (dx * dx + dy * dy)))
                best = min(best, math.hypot(lon - (x1 + t * dx), lat - (y1 + t * dy)))
    return best


def pole_of_inaccessibility(geom, steps=44, refine=3):
    """The interior point furthest from any boundary — keeps a marker off the district's edges."""
    x0, y0, x1, y1 = bbox_of(geom)
    best, best_d = None, -1.0
    for _ in range(refine):
        for i in range(steps + 1):
            for j in range(steps + 1):
                lon = x0 + (x1 - x0) * i / steps
                lat = y0 + (y1 - y0) * j / steps
                if not inside(lon, lat, geom):
                    continue
                d = seg_distance(lon, lat, geom)
                if d > best_d:
                    best, best_d = (lon, lat), d
        span_x, span_y = (x1 - x0) / steps, (y1 - y0) / steps
        x0, x1 = best[0] - span_x, best[0] + span_x
        y0, y1 = best[1] - span_y, best[1] + span_y
        steps = 10
    return best, best_d


def main():
    adm0 = fetch("tjk_ADM0.geojson", f"{GB}/ADM0/geoBoundaries-TJK-ADM0_simplified.geojson")
    adm1 = fetch("tjk_ADM1.geojson", f"{GB}/ADM1/geoBoundaries-TJK-ADM1_simplified.geojson")
    adm2 = fetch("tjk_ADM2.geojson", f"{GB}/ADM2/geoBoundaries-TJK-ADM2_simplified.geojson")
    ne_lakes = fetch("ne_10m_lakes.geojson", f"{NE}/ne_10m_lakes.geojson")
    ne_rivers = fetch("ne_10m_rivers_lake_centerlines.geojson", f"{NE}/ne_10m_rivers_lake_centerlines.geojson")
    sites = json.load(open(os.path.join(ROOT, "data", "tj-sites.json")))["sites"]

    country = adm0["features"][0]
    districts = {f["properties"]["shapeName"]: f["geometry"] for f in adm2["features"]}
    lon0, lat0, lon1, lat1 = bbox_of(country["geometry"])
    project, scale, height = make_projection(lon0, lat0, lon1, lat1, NAT_W, NAT_PAD)
    def in_country(geom):
        x0, y0, x1, y1 = bbox_of(geom)
        return x0 < lon1 and x1 > lon0 and y0 < lat1 and y1 > lat0

    rivers = [f for f in ne_rivers["features"]
              if f["properties"].get("name") in RIVERS and in_country(f["geometry"])]
    lakes = [f for f in ne_lakes["features"]
             if f["properties"].get("name") in LAKES and in_country(f["geometry"])]

    # anchor every site: an explicit city point, or the pole of inaccessibility of its district
    placed = []
    for s in sites:
        if s.get("point"):
            lat, lon = s["point"]
            note = s.get("pointSource", "city")
        else:
            geom = districts[s["adm2"]]
            (lon, lat), d = pole_of_inaccessibility(geom)
            note = "district"
            print(f"  {s['name']:12s} -> {s['adm2']:22s} {lat:.4f},{lon:.4f}  {d * 111:.0f} km from its boundary")
        if s.get("adm2") and not inside(lon, lat, districts[s["adm2"]]):
            print(f"  WARNING: {s['name']} falls outside {s['adm2']}")
        x, y = project(lon, lat)
        placed.append({**{k: v for k, v in s.items() if k != "point"},
                       "lat": round(lat, 4), "lon": round(lon, 4), "anchor": note,
                       "x": round(x, 1), "y": round(y, 1)})

    site_districts = [s["adm2"] for s in sites if s.get("adm2")]

    def layers(proj, min_area, tol):
        pick = lambda g: True
        return {
            "country": to_path(country["geometry"], proj, min_area, tol),
            "regions": "".join(to_path(f["geometry"], proj, min_area, tol)
                               for f in adm1["features"] if pick(f["geometry"])),
            "districts": "".join(to_path(g, proj, min_area, tol)
                                 for n, g in districts.items() if pick(g)),
            "siteDistricts": "".join(to_path(districts[n], proj, min_area, tol)
                                     for n in site_districts if pick(districts[n])),
            "rivers": "".join(to_line_path(f["geometry"], proj, tol) for f in rivers if pick(f["geometry"])),
            "lakes": [{"name": f["properties"]["name"], "d": to_path(f["geometry"], proj, min_area, tol)}
                      for f in lakes if pick(f["geometry"])],
        }

    national = layers(project, 1.0, 0.4)
    data = {
        "note": "Generated by tools/fetch_geo_tj.py.",
        "national": {"width": NAT_W, "height": round(height, 1), "bbox": [lon0, lat0, lon1, lat1],
                     "ptPerDeg": round(scale, 4), "kmPerPt": round(111.32 / scale, 5), **national},
        "sites": placed,
    }
    data["national"]["lakes"] = [l for l in data["national"]["lakes"] if l["d"]]

    out = os.path.join(ROOT, "data", "tajikistan-geo.json")
    with open(out, "w") as fh:
        json.dump(data, fh)
    print(f"wrote {out} ({os.path.getsize(out) / 1024:.0f} KB)")
    print(f"national {NAT_W:.0f}x{height:.0f}pt, {data['national']['kmPerPt']:.3f} km/pt")
    print("rivers:", [f["properties"]["name"] for f in rivers], "lakes:", [l["name"] for l in data["national"]["lakes"]])


if __name__ == "__main__":
    main()
