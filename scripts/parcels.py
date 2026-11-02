"""County of San Mateo parcel lookups (County GIS, free, no key).

    python scripts/parcels.py find "1700 S EL CAMINO"     search by situs address text
    python scripts/parcels.py owner "MIDPEN"              search by owner name
    python scripts/parcels.py apn 037-022-070            show one parcel
    python scripts/parcels.py fill SMC-000003            verify a record's APNs and fill missing outlines

`fill` stops with an error if any APN in the record isn't an active county parcel.
"""
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

URL = "https://gis.smcgov.org/maps/rest/services/Common/ACTIVE_PARCELS_APN/MapServer/0/query"
FIELDS = "APN,SITUS_ADDR,SITUS_CITY,COMBINEDOWNERNAMES,PUCDESC,documentnumber"
RECORDS = Path(__file__).resolve().parent.parent / "data" / "records"


def query(where, geometry=False, limit=25):
    params = {"where": where, "outFields": FIELDS, "returnGeometry": str(geometry).lower(),
              "outSR": "4326", "resultRecordCount": str(limit), "f": "json"}
    with urllib.request.urlopen(URL + "?" + urllib.parse.urlencode(params), timeout=60) as r:
        data = json.load(r)
    if "error" in data:
        sys.exit(f"County GIS error: {data['error']}")
    return data.get("features", [])


def fmt_apn(raw):
    d = "".join(ch for ch in raw if ch.isdigit())
    return f"{d[:3]}-{d[3:6]}-{d[6:9]}" if len(d) == 9 else raw


def show(features):
    for f in features:
        a = f["attributes"]
        print(f"{fmt_apn(a['APN'])}  {a['SITUS_ADDR']}  |  owner: {a['COMBINEDOWNERNAMES']}  |  {a['PUCDESC']}  |  doc {a['documentnumber']}")
    if not features:
        print("No matches.")


def esc(s):
    return s.replace("'", "''").upper()


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    cmd, arg = sys.argv[1], " ".join(sys.argv[2:])
    if cmd == "find":
        show(query(f"UPPER(SITUS_ADDR) LIKE '%{esc(arg)}%'"))
    elif cmd == "owner":
        show(query(f"UPPER(COMBINEDOWNERNAMES) LIKE '%{esc(arg)}%'"))
    elif cmd == "apn":
        show(query(f"APN='{''.join(c for c in arg if c.isdigit())}'"))
    elif cmd == "fill":
        path = RECORDS / f"{arg}.json"
        rec = json.loads(path.read_text(encoding="utf-8"))
        for p in rec.get("parcels", []):
            digits = "".join(c for c in p["apn"] if c.isdigit())
            feats = query(f"APN='{digits}'", geometry=True, limit=1)
            if not feats:
                sys.exit(f"{arg}: APN {p['apn']} is not an active San Mateo County parcel")
            a = feats[0]["attributes"]
            print(f"OK {p['apn']}  {a['SITUS_ADDR']}  owner: {a['COMBINEDOWNERNAMES']}  ({a['PUCDESC']})")
            if not p.get("outline"):
                ring = feats[0]["geometry"]["rings"][0]
                p["outline"] = [[round(x, 7), round(y, 7)] for x, y in ring]
        path.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{arg}: parcels verified, outlines filled")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
