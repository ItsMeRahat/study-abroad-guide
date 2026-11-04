"""Refresh every <CUR>_BDT exchange rate in data/**/facts.json (run monthly by GitHub Actions)."""
import pathlib
from guide_lib import ROOT, load, save, fx_to_bdt, today

for f in sorted(ROOT.glob("data/**/facts.json")):
    rel = str(f.relative_to(ROOT)); facts = load(rel); fx = facts.get("fx") or {}
    keys = [k for k in fx if k.endswith("_BDT")]
    for k in keys:
        try:
            fx[k] = round(fx_to_bdt(k[:3]), 4); fx["date"] = today(); fx["source"] = "open.er-api.com"
            print(rel, k, fx[k])
        except Exception as e:
            print("skip", rel, k, e)
    save(rel, facts)
