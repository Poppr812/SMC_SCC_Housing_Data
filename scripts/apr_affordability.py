"""Fill affordability from the state Annual Progress Report (APR) income breakdown.

Usage (from the repo root):
  python scripts/apr_affordability.py path/to/apr_raw.json           dry run: counts only
  python scripts/apr_affordability.py path/to/apr_raw.json --write   write claims into records

Only records that already cite an APR table are touched, and only facts they don't have yet:
- restricted_by_ami: deed-restricted units by state income category (acutely low 15%, extremely
  low 30%, very low 50%, low 80%, moderate 120% AMI), from the APR row and stage (application,
  entitlement, permit, completion) reporting the most deed-restricted units.
- affordability_type: "Market-rate" when no row reports any deed-restricted unit (unrestricted is
  market, including units the city reported as low or moderate income without a restriction);
  otherwise "100% affordable" (all but managers' units) or "Mixed-income".
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import import_apr as A  # noqa: E402
import parcels  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CATS = [("ACUTELY_LOW_INCOME", 15), ("EXTREMELY_LOW_INCOME", 30), ("VLOW_INCOME", 50), ("LOW_INCOME", 80), ("MOD_INCOME", 120)]
STAGES = {"A": [("", "application")], "A2": [("", "entitlement"), ("BP_", "building permit"), ("CO_", "completion")]}


def best_vector(rows):
    """(total deed-restricted, [(count, ami)], year, table, stage) with the most restricted units; None if no A2 row."""
    best = None
    for r in rows:
        for pre, stage in STAGES[r["_t"]]:
            vec = [(A.n(r.get(pre + c + "_DR")), ami) for c, ami in CATS]
            tot = sum(x for x, _ in vec)
            key = (tot, r["_t"] == "A2", str(r.get("YEAR")))
            if best is None or key > best[0]:
                best = (key, tot, [{"count": x, "ami": ami} for x, ami in vec if x], r.get("YEAR"), r["_t"], stage)
    return best[1:] if best else None


def main():
    raw = json.load(open(sys.argv[1], encoding="utf-8"))
    write = "--write" in sys.argv
    groups = A.rollup(raw)
    sources = {p.stem: json.load(open(p, encoding="utf-8")) for p in (ROOT / "data" / "sources").glob("SRC-*.json")}
    apr_src = {sid: s for sid, s in sources.items() if s["title"].startswith("Housing Element Annual Progress Report")}

    records, index = {}, {}
    for f in (ROOT / "data" / "records").glob("*.json"):
        r = json.load(open(f, encoding="utf-8"))
        cited = set()
        def walk(x):
            if isinstance(x, dict):
                for k, v in x.items():
                    if k == "src" and isinstance(v, list):
                        cited.update(v)
                    else:
                        walk(v)
            elif isinstance(x, list):
                for v in x:
                    walk(v)
        walk(r)
        mine = {s for s in cited if s in apr_src}
        if not mine:
            continue
        records[r["id"]] = (f, r, mine)
        jur = (A_best := r["facts"]["jurisdiction"]["claims"][0]["value"]).upper()
        for p in r["parcels"]:
            index.setdefault(("ap", parcels.digits(p["apn"])), set()).add(r["id"])
        for a in r.get("addresses", []):
            index.setdefault(("ad", jur, A.norm(a["text"].split(",")[0])), set()).add(r["id"])

    stats = {"matched": 0, "type_market": 0, "type_affordable": 0, "ami_added": 0, "ambiguous": 0, "no_a2": 0}  # no_a2 = matched with application rows only
    done = set()
    for p in groups:
        juris = p["juris"].upper()
        juris = "UNINCORPORATED" if juris.endswith(" COUNTY") else juris
        hits = set()
        for t in p["apns"]:
            hits |= index.get(("ap", parcels.digits(t)), set())
        for a in p["addresses"]:
            hits |= index.get(("ad", juris, A.norm(a)), set())
        if len(hits) != 1:
            stats["ambiguous"] += len(hits) > 1
            continue
        rid = hits.pop()
        if rid in done:
            continue
        done.add(rid)
        f, r, mine = records[rid]
        vec = best_vector(p["rows"])
        if not vec:
            continue
        if not any(x["_t"] == "A2" for x in p["rows"]):
            stats["no_a2"] += 1  # application rows only: still a stated breakdown, noted as the application stage
        stats["matched"] += 1
        tot, ami, year, table, stage = vec
        want = "Table A2" if table == "A2" else "Table A ("
        sid = next((s for s in sorted(mine) if want in apr_src[s]["title"]), sorted(mine)[0])
        facts, changed = r["facts"], False
        if tot and "restricted_by_ami" not in facts:
            facts["restricted_by_ami"] = {"claims": [{"value": ami, "src": [sid],
                "note": f"State report {year}, {stage} stage: deed-restricted units by state income category (AMI is the category's upper limit)"}]}
            stats["ami_added"] += 1
            changed = True
        if "affordability_type" not in facts:
            units = A.n((facts.get("total_units") or {}).get("claims", [{}])[0].get("value")) if facts.get("total_units") else 0
            if tot == 0:
                val, note = "Market-rate", (f"State report (through {max(str(x.get('YEAR')) for x in p['rows'])}): no deed-restricted units reported "
                                            "at any stage. A later source showing restricted units would override this.")
                stats["type_market"] += 1
            else:
                val = "100% affordable" if units and tot >= units - 3 else "Mixed-income"
                note = f"State report {year}, {stage} stage: {tot} deed-restricted units"
                stats["type_affordable"] += 1
            facts["affordability_type"] = {"claims": [{"value": val, "src": [sid], "note": note}]}
            changed = True
        if changed and write:
            with open(f, "w", encoding="utf-8", newline="\n") as fh:
                json.dump(r, fh, indent=2, ensure_ascii=False)
                fh.write("\n")
    print(("WROTE " if write else "DRY RUN ") + json.dumps(stats))


if __name__ == "__main__":
    main()
