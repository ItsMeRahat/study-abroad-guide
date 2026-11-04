"""Import QS / THE ranks into data/rankings.json.

    python scripts/update_rankings.py qs 2027 <csv-file | json-url | json-file>
    python scripts/update_rankings.py the 2027 <csv-file | json-url | json-file>

CSV: needs a name column (name/institution/university/title) and a rank column (rank/rank_display/overall rank).
JSON: the first list of objects that has a name-like and a rank-like key is used (QS and THE ranking feeds both fit).
Download QS results from topuniversities.com or THE data from timeshighereducation.com, then pass the file here.
Imported rows are merged into the provider table (matching names are overwritten); sources are stored per entry. Check the diff before committing.
"""
import sys, csv, io, json, pathlib
from guide_lib import ROOT, load, save, get, norm, rank_num, today

NAME = ("name", "institution", "university", "title"); RANK = ("rank", "rank_display", "overall rank", "overall_rank")

def rows_from(obj):
    if isinstance(obj, list) and obj and isinstance(obj[0], dict):
        low = {k.lower() for k in obj[0]}
        if low & set(NAME) and low & set(RANK):
            return obj
    kids = obj.values() if isinstance(obj, dict) else obj if isinstance(obj, list) else []
    for v in kids:
        r = rows_from(v)
        if r:
            return r
    return None

def read(src):
    text = get(src) if src.startswith("http") else pathlib.Path(src).read_text(encoding="utf-8-sig")
    try:
        rows = rows_from(json.loads(text))
    except ValueError:
        rows = list(csv.DictReader(io.StringIO(text)))
    if not rows:
        sys.exit("No rows with a name and a rank column were found in " + src)
    out = {}
    for r in rows:
        low = {k.lower().strip(): v for k, v in r.items()}
        name = next((low[k] for k in NAME if low.get(k)), None); rk = next((low[k] for k in RANK if low.get(k)), None)
        if name and rk and rank_num(rk):
            out[norm(name)] = {"name": str(name).strip(), "r": str(rk).strip(), "n": rank_num(rk), "src": src if src.startswith("http") else ""}
    return out

if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] not in ("qs", "the"):
        sys.exit(__doc__)
    prov, edition, src = sys.argv[1:]
    data = load("data/rankings.json")
    new = read(src)
    old = data["ranks"].get(prov, {})
    for k, v in new.items():
        v["src"] = v["src"] or data["providers"][prov]["url"]
        if k in old and old[k].get("note") and old[k].get("r") == v["r"]:
            v["note"] = old[k]["note"]
    merged = dict(old); merged.update(new)  # merge: a partial file never wipes existing entries
    data["ranks"][prov] = merged; data["providers"][prov]["edition"] = edition; data["updated"] = today()
    save("data/rankings.json", data)
    print("%s %s: %d rows imported, table now holds %d institutions (was %d)." % (prov.upper(), edition, len(new), len(merged), len(old)))
