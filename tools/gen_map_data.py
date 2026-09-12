"""Generate the world-map assets used by the day/night map on the planner.

Produces two small files in assets/:

  world-land.json   land outlines as SVG path data in a 360x180 equirectangular
                    space (x = lon+180, y = 90-lat), so the client scales it to
                    whatever width it renders at.
  zone-points.json  IANA zone -> [lat, lon], from the tz database's own
                    zone1970.tab. Used as a fallback position for any city whose
                    real coordinates we do not have (URL-restored cities, the
                    local seed list). Search results carry real coordinates.

Source: Natural Earth 110m land, public domain (CC0). No attribution required,
though the project is credited in MAINTENANCE.md anyway.

Deliberately NO time zone boundaries. Real zone borders are jagged and
political - China spans five geographic bands on one zone, Nepal is +5:45 - so
a drawn boundary map would be approximate in a way that undercuts a site that
hedges moon-sighting holidays for accuracy. City dots and a computed day/night
terminator claim only two things, both exactly true: these cities are here, and
it is night here.

Usage:  python tools/gen_map_data.py
"""
import json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CACHE = os.path.join(HERE, ".cache")
ASSETS = os.path.join(REPO, "assets")
LAND_URL = ("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
            "master/geojson/ne_110m_land.geojson")
ZONE_TAB_URL = "https://raw.githubusercontent.com/eggert/tz/main/zone1970.tab"

# Drop specks that are invisible at the sizes this renders at, in square degrees.
MIN_AREA = 1.2
PRECISION = 1  # decimal places; ~11 km, far finer than one screen pixel here


def fetch(url, name):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, name)
    if not os.path.exists(path):
        req = urllib.request.Request(url, headers={"User-Agent": "findcommonhours-build"})
        with urllib.request.urlopen(req, timeout=120) as r:
            open(path, "wb").write(r.read())
    return path


def ring_area(ring):
    """Shoelace, in square degrees. Only used to discard specks."""
    a = 0.0
    for i in range(len(ring) - 1):
        a += ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1]
    return abs(a) / 2.0


def ring_to_path(ring):
    pts, last = [], None
    for lon, lat in ring:
        x = round(lon + 180, PRECISION)
        y = round(90 - lat, PRECISION)
        if (x, y) == last:      # collapse points that round to the same spot
            continue
        pts.append((x, y)); last = (x, y)
    if len(pts) < 3:
        return None
    d = f"M{pts[0][0]} {pts[0][1]}" + "".join(f"L{x} {y}" for x, y in pts[1:]) + "Z"
    return d


def build_land():
    geo = json.load(open(fetch(LAND_URL, "ne_110m_land.geojson"), encoding="utf-8"))
    paths, dropped = [], 0
    for feat in geo["features"]:
        g = feat["geometry"]
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        for poly in polys:
            for ring in poly:          # ring 0 is outer, rest are holes
                if ring_area(ring) < MIN_AREA:
                    dropped += 1
                    continue
                d = ring_to_path(ring)
                if d:
                    paths.append(d)
    return paths, dropped


def build_zone_points():
    out = {}
    for line in open(fetch(ZONE_TAB_URL, "zone1970.tab"), encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        f = line.rstrip("\n").split("\t")
        if len(f) < 3:
            continue
        coords, zone = f[1], f[2]
        # ISO 6709: +DDMM+DDDMM or +DDMMSS+DDDMMSS
        sign1 = 1 if coords[0] == "+" else -1
        rest = coords[1:]
        split = next((i for i, c in enumerate(rest) if c in "+-"), None)
        if split is None:
            continue
        latpart, lonpart = rest[:split], rest[split:]
        sign2 = 1 if lonpart[0] == "+" else -1
        lonpart = lonpart[1:]

        def dm(s, deg_digits):
            deg = int(s[:deg_digits]); mn = int(s[deg_digits:deg_digits + 2])
            sec = int(s[deg_digits + 2:deg_digits + 4]) if len(s) >= deg_digits + 4 else 0
            return deg + mn / 60 + sec / 3600

        out[zone] = [round(sign1 * dm(latpart, 2), 3), round(sign2 * dm(lonpart, 3), 3)]
    return out


def main():
    os.makedirs(ASSETS, exist_ok=True)
    paths, dropped = build_land()
    land_path = os.path.join(ASSETS, "world-land.json")
    json.dump({"viewBox": "0 0 360 180", "paths": paths},
              open(land_path, "w", encoding="utf-8"), separators=(",", ":"))

    zones = build_zone_points()
    zone_path = os.path.join(ASSETS, "zone-points.json")
    json.dump(zones, open(zone_path, "w", encoding="utf-8"), separators=(",", ":"))

    print(f"  world-land.json   {len(paths)} paths, {dropped} specks dropped, "
          f"{os.path.getsize(land_path):,} bytes")
    print(f"  zone-points.json  {len(zones)} zones, {os.path.getsize(zone_path):,} bytes")


if __name__ == "__main__":
    main()
