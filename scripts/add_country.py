"""Add a country to the repository from original sources.

    python scripts/add_country.py DK            # ISO 3166-1 alpha-2 code

Sources: REST Countries (profile), open.er-api.com (BDT rate), Wikidata SPARQL (universities that have an
official website), data/rankings.json (QS/THE ranks matched by name). Writes data/<code>/{facts,universities,
content}.json and registers the country in data/countries.json. Tuition, visa and deadline facts are NOT scraped:
they differ by programme and change often, so the page tells the reader to confirm them on official sites.
"""
import sys
from guide_lib import ROOT, load, save, get_json, get, fx_to_bdt, today, norm

SPARQL = """SELECT ?u (SAMPLE(?l) AS ?n) (SAMPLE(?w) AS ?web) (SAMPLE(?cl) AS ?city) WHERE {
 ?c wdt:P297 "%s". ?u wdt:P31/wdt:P279* wd:Q3918; wdt:P17 ?c; wdt:P856 ?w; rdfs:label ?l.
 FILTER(LANG(?l)="en") FILTER NOT EXISTS { ?u wdt:P576 ?x }
 OPTIONAL { ?u wdt:P131 ?ci. ?ci rdfs:label ?cl. FILTER(LANG(?cl)="en") } } GROUP BY ?u LIMIT 400"""

def universities(cc):
    rows = get_json("https://query.wikidata.org/sparql", {"format": "json", "query": SPARQL % cc})["results"]["bindings"]
    seen, out = set(), []
    for b in rows:
        name = b["n"]["value"]
        if name.startswith("Q") and name[1:].isdigit() or norm(name) in seen:
            continue
        seen.add(norm(name))
        out.append({"id": norm(name).replace(" ", "-"), "name": name, "city": b.get("city", {}).get("value", "See website"),
                    "website": b["web"]["value"], "top10": False})
    return sorted(out, key=lambda u: u["name"])

def build(cc):
    c = get_json("https://restcountries.com/v3.1/alpha/" + cc, {"fields": "name,cca2,flag,currencies,capital,region,subregion,population,languages"})
    c = c[0] if isinstance(c, list) else c
    name, cur = c["name"]["common"], next(iter(c.get("currencies") or {"USD": 0}))
    rate = fx_to_bdt(cur); unis = universities(cc.upper())
    facts = {"last_checked": today(), "maintenance": {}, "institutions": {"listed": len(unis)}, "links": {},
             "fx": {cur + "_BDT": round(rate, 4), "date": today(), "source": "open.er-api.com"}}
    rows = [("Capital", ", ".join(c.get("capital") or ["n/a"])), ("Region", c.get("subregion") or c.get("region", "")),
            ("Languages", ", ".join((c.get("languages") or {}).values())), ("Population", "{:,}".format(c.get("population", 0))),
            ("Currency", cur), ("Exchange rate", "1 %s = %.2f BDT (%s)" % (cur, rate, today()))]
    dl = "".join("<dt>%s</dt><dd>%s</dd>" % r for r in rows)
    ov = ('<div class="card"><div class="bd" style="border:0;padding:0"><dl>%s</dl></div></div><div class="note">Auto-built entry: profile, '
          'exchange rate and university list come from REST Countries, open.er-api.com and Wikidata. Entry requirements, fees, '
          'deadlines, visa rules and scholarships are not auto-filled; confirm them on each university site and the national immigration authority.</div>' % dl)
    meta = {"code": cc.lower(), "name": name, "flag": c.get("flag", ""), "currency": cur, "title": "Study in %s: Applicant Guide" % name,
            "sub": "Bangladesh applicants · Universities, rankings, application, visa and money.", "portal": "Wikidata",
            "portal_url": "https://www.wikidata.org/wiki/Special:Search?search=" + name.replace(" ", "+") + "+university",
            "top_label": "", "uni_title": name + " universities", "prog_btn": "University website",
            "list_note": "Universities come from Wikidata (institutions with an official website).", "rank_note": "",
            "gen_note": "Entry requirements, tuition fees and scholarships differ by programme. Open the university website and confirm with the official source.",
            "caution": "<b>Auto-built entry:</b> verify every figure with the official source before advising a student."}
    content = {"meta": meta, "tabs": [["overview", "Overview"], ["unis", "Universities"]], "links": {}, "req": {}, "steps": [],
               "sections": {"overview": {"title": "Overview", "html": ov}}}
    return meta, facts, {"source": "https://www.wikidata.org/", "universities": unis}, content

if __name__ == "__main__":
    if len(sys.argv) != 2 or len(sys.argv[1]) != 2:
        sys.exit(__doc__)
    cc = sys.argv[1].lower()
    meta, facts, unis, content = build(cc)
    for n, o in (("facts", facts), ("universities", unis), ("content", content)):
        save("data/%s/%s.json" % (cc, n), o)
    cs = [x for x in load("data/countries.json") if x["code"] != cc]
    cs.append({"code": cc, "name": meta["name"], "flag": meta["flag"], "dir": cc, "currency": meta["currency"]})
    save("data/countries.json", cs)
    print("Added %s with %d universities. Now run: python scripts/update_rankings.py --match" % (meta["name"], len(unis["universities"])))
