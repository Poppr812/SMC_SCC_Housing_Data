"""County parcel lookups (free public GIS, no key). San Mateo by default; add --scc for Santa Clara.

    python scripts/parcels.py find "1700 S EL CAMINO"     search by situs address text
    python scripts/parcels.py find "905 N CAPITOL" --scc
    python scripts/parcels.py owner "MIDPEN"              search by owner name (San Mateo only)
    python scripts/parcels.py apn 037-022-070             show one parcel
    python scripts/parcels.py apn 254-29-028 --scc
    python scripts/parcels.py at 37.56 -122.32            parcel at a point (add --scc for Santa Clara)
    python scripts/parcels.py fill SMC-000003             verify a record's APNs and fill missing outlines

`fill` stops with an error if any APN in the record isn't an active county parcel.
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

SMC_URL = "https://gis.smcgov.org/maps/rest/services/Common/ACTIVE_PARCELS_APN/MapServer/0/query"
SMC_FIELDS = "APN,SITUS_ADDR,SITUS_CITY,COMBINEDOWNERNAMES,PUCDESC,documentnumber"
SCC_URL = "https://data.sccgov.org/resource/ubcd-cewv.json"
SCC_FIELDS = "apn,situs_house_number,situs_street_direction,situs_street_name,situs_street_type,situs_city_name,jurisdiction"
RECORDS = Path(__file__).resolve().parent.parent / "data" / "records"


def _get(url, params):
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url + "?" + urllib.parse.urlencode(params), timeout=60) as r:
                return json.load(r)
        except OSError:  # county servers time out now and then
            if attempt == 3:
                raise
            time.sleep(5 * (attempt + 1))


def smc_query(where=None, geometry=False, limit=25, point=None):
    params = {"outFields": SMC_FIELDS, "returnGeometry": str(geometry).lower(),
              "outSR": "4326", "resultRecordCount": str(limit), "f": "json"}
    if point:
        params.update({"geometry": f"{point[1]},{point[0]}", "geometryType": "esriGeometryPoint",
                       "inSR": "4326", "spatialRel": "esriSpatialRelIntersects", "where": "1=1"})
    else:
        params["where"] = where
    data = _get(SMC_URL, params)
    if "error" in data:
        raise RuntimeError(f"County GIS error: {data['error']}")
    return data.get("features", [])


def scc_query(where, geometry=False, limit=25):
    select = SCC_FIELDS + (",the_geom" if geometry else "")
    return _get(SCC_URL, {"$select": select, "$where": where, "$limit": str(limit)})


def digits(apn):
    return "".join(c for c in str(apn) if c.isdigit())


def fmt_apn(raw, county="SMC"):
    d = digits(raw)
    if county == "SCC":
        return f"{d[:3]}-{d[3:5]}-{d[5:8]}" if len(d) == 8 else str(raw)
    return f"{d[:3]}-{d[3:6]}-{d[6:9]}" if len(d) == 9 else str(raw)


def _scc_situs(a):
    parts = [a.get("situs_house_number"), a.get("situs_street_direction"), a.get("situs_street_name"), a.get("situs_street_type")]
    return " ".join(p for p in parts if p) + (", " + a["situs_city_name"] if a.get("situs_city_name") else "")


def _scc_ring(a):
    polys = (a.get("the_geom") or {}).get("coordinates") or []
    return max((p[0] for p in polys), key=len) if polys else None


def lookup(county, apn=None, point=None):
    """One parcel as {apn, situs, owner, outline}, or None."""
    if county == "SCC":
        where = f"apn='{digits(apn)}'" if apn else f"apn IS NOT NULL AND intersects(the_geom,'POINT({point[1]} {point[0]})')"
        rows = scc_query(where, geometry=True, limit=1)
        if not rows:
            return None
        ring = _scc_ring(rows[0])
        return {"apn": fmt_apn(rows[0]["apn"], "SCC"), "situs": _scc_situs(rows[0]), "owner": "",
                "outline": [[round(x, 7), round(y, 7)] for x, y in ring] if ring else None}
    feats = smc_query(f"APN='{digits(apn)}'", geometry=True, limit=1) if apn else smc_query(geometry=True, limit=1, point=point)
    if not feats:
        return None
    a = feats[0]["attributes"]
    ring = feats[0]["geometry"]["rings"][0]
    return {"apn": fmt_apn(a["APN"]), "situs": a["SITUS_ADDR"], "owner": a["COMBINEDOWNERNAMES"],
            "outline": [[round(x, 7), round(y, 7)] for x, y in ring]}


def show_smc(features):
    for f in features:
        a = f["attributes"]
        print(f"{fmt_apn(a['APN'])}  {a['SITUS_ADDR']}  |  owner: {a['COMBINEDOWNERNAMES']}  |  {a['PUCDESC']}  |  doc {a['documentnumber']}")
    if not features:
        print("No matches.")


def show_scc(rows):
    for a in rows:
        print(f"{fmt_apn(a['apn'], 'SCC')}  {_scc_situs(a)}  |  jurisdiction: {a.get('jurisdiction')}")
    if not rows:
        print("No matches.")


def esc(s):
    return s.replace("'", "''").upper()


def scc_find(text):
    m = re.match(r"\s*(\d+)\s+(?:([NSEW])\.?\s+)?(.+)", text.upper())
    if not m:
        return scc_query(f"upper(situs_street_name) like '%{esc(text)}%'")
    street = re.sub(r"\s+(ST|STREET|AV|AVE|AVENUE|RD|ROAD|BL|BLVD|BOULEVARD|DR|DRIVE|WY|WAY|LN|LANE|CT|COURT|PL|PLACE)\.?$", "", m.group(3).strip())
    where = f"situs_house_number='{m.group(1)}' AND upper(situs_street_name) like '%{esc(street)}%'"
    if m.group(2):
        where += f" AND situs_street_direction='{m.group(2)}'"
    return scc_query(where)


def main():
    args = [a for a in sys.argv[1:] if a != "--scc"]
    county = "SCC" if "--scc" in sys.argv else "SMC"
    if len(args) < 2:
        sys.exit(__doc__)
    cmd, arg = args[0], " ".join(args[1:])
    if cmd == "find":
        show_scc(scc_find(arg)) if county == "SCC" else show_smc(smc_query(f"UPPER(SITUS_ADDR) LIKE '%{esc(arg)}%'"))
    elif cmd == "owner":
        if county == "SCC":
            sys.exit("The Santa Clara parcel data has no owner names.")
        show_smc(smc_query(f"UPPER(COMBINEDOWNERNAMES) LIKE '%{esc(arg)}%'"))
    elif cmd == "apn":
        show_scc(scc_query(f"apn='{digits(arg)}'")) if county == "SCC" else show_smc(smc_query(f"APN='{digits(arg)}'"))
    elif cmd == "at":
        p = lookup(county, point=(float(args[1]), float(args[2])))
        print(f"{p['apn']}  {p['situs']}  owner: {p['owner']}" if p else "No parcel there.")
    elif cmd == "fill":
        path = RECORDS / f"{arg}.json"
        rec = json.loads(path.read_text(encoding="utf-8"))
        county = arg[:3]
        for p in rec.get("parcels", []):
            found = lookup(county, apn=p["apn"])
            if not found:
                sys.exit(f"{arg}: APN {p['apn']} is not an active {county} parcel")
            print(f"OK {p['apn']}  {found['situs']}  owner: {found['owner']}")
            if not p.get("outline"):
                p["outline"] = found["outline"]
        path.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{arg}: parcels verified, outlines filled")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
