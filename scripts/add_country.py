"""Generate a permanent country guide scaffold from structured public sources.

Usage: python scripts/add_country.py CA
The script creates data/<code>/{facts,universities,content}.json and registers the country.
Country profile/currency/university directory are auto-collected. Country-specific admissions,
tuition, immigration, scholarship and work rules are explicitly marked for official verification;
the script never invents those values.
"""
import sys, urllib.parse, html
from guide_lib import ROOT, load, save, get_json, fx_to_bdt, today, norm

COUNTRIES_URL = "https://cdn.jsdelivr.net/gh/mledoze/countries@master/countries.json"
SPARQL = """SELECT ?u (SAMPLE(?l) AS ?n) (SAMPLE(?w) AS ?web) (SAMPLE(?cl) AS ?city) WHERE {
 ?c wdt:P297 "%s". ?u wdt:P31/wdt:P279* wd:Q3918; wdt:P17 ?c; wdt:P856 ?w; rdfs:label ?l.
 FILTER(LANG(?l)="en") FILTER NOT EXISTS { ?u wdt:P576 ?x }
 OPTIONAL { ?u wdt:P131 ?ci. ?ci rdfs:label ?cl. FILTER(LANG(?cl)="en") }
} GROUP BY ?u LIMIT 400"""

def flag_emoji(code):
    return "".join(chr(127397 + ord(ch)) for ch in code.upper())

def country_record(cc):
    rows = get_json(COUNTRIES_URL)
    for c in rows:
        if (c.get("cca2") or "").lower() == cc:
            return c
    raise SystemExit("Unknown ISO-3166 alpha-2 country code: " + cc.upper())

def world_bank_population(cc):
    url = "https://api.worldbank.org/v2/country/%s/indicator/SP.POP.TOTL" % cc.upper()
    try:
        payload = get_json(url, {"format": "json", "per_page": 70})
        rows = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
        valid = [x for x in rows if x.get("value") is not None]
        if not valid:
            return None, None
        latest = max(valid, key=lambda x: int(x.get("date", 0)))
        return int(latest["value"]), latest["date"]
    except Exception as exc:
        print("WARNING: World Bank population lookup failed:", exc)
        return None, None

def world_bank_population(cc):
    url = "https://api.worldbank.org/v2/country/%s/indicator/SP.POP.TOTL" % cc.upper()
    try:
        payload = get_json(url, {"format": "json", "per_page": 70})
        rows = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
        valid = [x for x in rows if x.get("value") is not None]
        if not valid:
            return None, None
        latest = max(valid, key=lambda x: int(x.get("date", 0)))
        return int(latest["value"]), latest["date"]
    except Exception as exc:
        print("WARNING: World Bank population lookup failed:", exc)
        return None, None

def universities(cc):
    params = {"format": "json", "query": SPARQL % cc.upper()}
    endpoints = ["https://qlever.dev/api/wikidata", "https://query.wikidata.org/sparql"]
    last = None
    for endpoint in endpoints:
        try:
            data = get_json(endpoint, params)
            bindings = data.get("results", {}).get("bindings", [])
            seen, out = set(), []
            for b in bindings:
                name = b.get("n", {}).get("value", "")
                web = b.get("web", {}).get("value", "")
                if not name or not web or norm(name) in seen:
                    continue
                if name.startswith("Q") and name[1:].isdigit():
                    continue
                seen.add(norm(name))
                out.append({
                    "id": norm(name).replace(" ", "-"),
                    "name": name,
                    "city": b.get("city", {}).get("value", "See official website"),
                    "website": web,
                    "top10": False,
                    "profile": {},
                    "profile_source": "University directory record from Wikidata; verify institution status and programme details on the official website."
                })
            return sorted(out, key=lambda x: x["name"]), endpoint
        except Exception as exc:
            last = exc
    print("WARNING: university directory lookup failed:", last)
    return [], ""

def section(title, body):
    return {"title": title, "html": body}

def build(cc):
    c = country_record(cc)
    name = c["name"]["common"]
    currencies = c.get("currencies") or {}
    cur = next(iter(currencies), "USD")
    currency_name = currencies.get(cur, {}).get("name", cur)
    capitals = c.get("capital") or []
    langs = list((c.get("languages") or {}).values())
    rate = None
    try:
        rate = round(fx_to_bdt(cur), 4)
    except Exception as exc:
        print("WARNING: exchange rate unavailable:", exc)
    population = c.get("population") or None\n    population_year = None\n    if not population:\n        population, population_year = world_bank_population(cc)\n    population = c.get("population") or None
    population_year = None
    if not population:
        population, population_year = world_bank_population(cc)
    unis, uni_source = universities(cc)

    facts = {
        "last_checked": today(),
        "data_status": "needs_official_verification",
        "population": population,
        "population_year": population_year,
        "population_source": "https://api.worldbank.org/v2/country/%s/indicator/SP.POP.TOTL" % cc.upper(),\n        "population": population,\n        "population_year": population_year,\n        "population_source": "https://api.worldbank.org/v2/country/%s/indicator/SP.POP.TOTL" % cc.upper(),
        "intake": "Varies by institution and programme; verify official deadlines.",
        "dates": {"source": "", "rows": [
            {"date": "Verify with institution", "event": "Application opening and deadline vary by university, programme and intake."},
            {"date": "After admission", "event": "Check the official offer acceptance, deposit and enrolment deadlines."}
        ]},
        "maintenance": {"monthly": 0, "annual": 0, "source": ""},
        "institutions": {"listed": len(unis), "source": "https://www.wikidata.org/"},
        "fees": {},
        "work_hours_per_week": None,
        "permit_wait": {"note": "Not yet verified. Check the official immigration authority."},
        "fx": ({cur + "_BDT": rate, "date": today(), "source": "open.er-api.com"} if rate else {"date": today(), "source": "Unavailable; retry later"}),
        "links": {"programme_search": "", "note": "Add official national study portal and immigration links after verification."},
        "sources": {
            "country_profile": COUNTRIES_URL,
            "universities": uni_source or "https://www.wikidata.org/",
            "exchange_rate": "https://open.er-api.com/"
        }
    }

    safe_name = html.escape(name)
    rows = [
        ("Capital", ", ".join(capitals) or "Not listed"),
        ("Region", c.get("subregion") or c.get("region") or "Not listed"),
        ("Languages", ", ".join(langs) or "Not listed"),
        ("Population", ("{:,}".format(population) + ((" (" + str(population_year) + " estimate)") if population_year else "")) if population else "Unavailable"),
        ("Currency", cur + " — " + currency_name),
        ("Exchange rate", ("1 %s = %.4f BDT (%s)" % (cur, rate, today())) if rate else "Currently unavailable")
    ]
    profile_html = '<div class="card"><dl>' + "".join("<dt>%s</dt><dd>%s</dd>" % (html.escape(k), html.escape(v)) for k,v in rows) + "</dl></div>"
    warning = '<div class="note warn"><b>Verification required:</b> This country profile and university directory are automatically collected. Admission rules, Bangladesh credential equivalency, English waivers, tuition, proof of funds, visa rules, work rights, post-study routes and scholarships are not assumed. Each must be checked against the current official government or university source before relying on it.</div>'
    overview = profile_html + warning + '<h3>Admission overview</h3><div class="card"><p>Choose Bachelor’s or Master’s and check the official university programme page. Country-specific Bangladesh entry requirements have not yet been verified.</p><div class="seg" id="lvl"><button aria-pressed="true" data-l="ug">Bachelor’s (UG)</button><button aria-pressed="false" data-l="pg">Master’s (PG)</button></div><dl id="req"></dl></div><p class="links"><a href="https://www.wikidata.org/" target="_blank" rel="noopener">University data source</a></p>'
    apply = '<p>Application steps depend on the institution and programme. Use this checklist as a preparation guide, not as a country-specific deadline guarantee.</p><div class="bar"><i id="pb"></i></div><ol class="steps" id="st"></ol><div class="note warn">Official application portal and country-specific deadlines: <b>Needs verification</b>.</div>'
    eng = '<details open><summary>English language tests</summary><div><p>IELTS Academic, TOEFL iBT, PTE Academic and other accepted tests and scores vary by institution and programme. No national score or MOI waiver is assumed.</p></div></details><details><summary>Bangladesh study-gap and credential assessment</summary><div><p>Country-specific HSC, Bachelor’s equivalency, study-gap policy and MOI waiver rules: <b>Needs official verification</b>. Obtain written confirmation from the university.</p></div></details>'
    money = '<details open><summary>Tuition and living costs</summary><div><p>Fees differ by institution, level, programme and intake. No country-wide tuition figure is assumed.</p></div></details><div class="card"><h3>Budget conversion</h3><label for="mo">Number of months</label><input id="mo" type="number" min="1" max="48" value="12"><p id="tot">Local currency amount: Needs verification</p><p id="bdt">BDT conversion will use the available exchange rate.</p><small id="fxn">Exchange rate is indicative and may change.</small></div><div class="note warn">Official proof-of-funds amount and accepted evidence: <b>Needs verification</b>.</div>'
    visa = '<details open><summary>Student visa / residence permit</summary><div><p>Permit type, eligibility, application portal, fees, biometrics, medical checks, financial evidence and processing times must be verified on the country’s official immigration website.</p></div></details><div class="note warn">Official immigration source: <b>Needs verification</b>. Do not rely on third-party guarantees.</div>'
    after = '<details open><summary>Work during study</summary><div><p>Work-hour limits and eligibility depend on local law and permit conditions. <b>Needs official verification.</b></p></div></details><details><summary>Post-study work and residence</summary><div><p>Graduate work routes, eligible qualifications, duration and application windows: <b>Needs official verification.</b></p></div></details>'
    schol = '<details open><summary>Scholarships and funding</summary><div><p>University awards, government scholarships, eligibility, funding amount and deadlines must be checked on the official award provider’s website.</p></div></details>'
    meta = {
        "code": cc, "name": name, "flag": flag_emoji(cc), "currency": cur,
        "title": "Study in " + name + ": Applicant Guide",
        "sub": "Bangladesh applicants · Universities, admission, costs, visa and scholarships.",
        "portal": "University directory", "portal_url": "https://www.wikidata.org/",
        "top_label": "Ranked", "uni_title": name + " universities",
        "prog_btn": "Official university website",
        "list_note": "Directory records are sourced from Wikidata and may be incomplete. Confirm official recognition and programme availability.",
        "rank_note": "Only ranks present in the maintained QS/THE dataset are displayed. No rank is inferred.",
        "gen_note": "University directory data is automatically collected. Confirm every programme, fee and entry requirement on the official university website.",
        "caution": "<b>Automatically generated country guide:</b> profile and university directory are collected from public datasets. All country-specific admission, immigration, financial and scholarship information must be verified from official sources before use."
    }
    content = {
        "meta": meta,
        "tabs": [["overview","Overview"],["unis","Universities"],["apply","Apply"],["eng","English & gap"],["money","Money"],["visa","Study permit"],["after","After study"],["schol","Scholarships"]],
        "links": {}, "req": {
            "ug": [["Academic qualification","Bangladesh HSC equivalency and subject prerequisites: Needs official university verification."],["Grades","Minimum grades and selection method: Needs official university verification."],["English","Accepted tests and scores vary by programme; verify with the institution."],["Documents","Follow the target university’s current international applicant checklist."]],
            "pg": [["Academic qualification","Bachelor’s degree equivalency, duration and subject prerequisites: Needs official university verification."],["Grades","Minimum GPA and grading conversion: Needs official university verification."],["English","Accepted tests and scores vary by programme; verify with the institution."],["Documents","Degree certificate, transcripts, CV, statement and references as required by the programme."]]
        },
        "steps": [
            "Choose the degree level, subject, institution and intake.",
            "Check the official programme page for Bangladesh academic equivalency and subject prerequisites.",
            "Confirm English test, score, MOI waiver and validity rules directly with the institution.",
            "Prepare certificates, transcripts, passport, references, CV, statement and certified translations if required.",
            "Apply through the official university or national application portal before its published deadline.",
            "Compare the written offer, tuition, deposit and refund policy; verify the institution is officially recognised.",
            "Check the official immigration authority’s student permit requirements and financial evidence.",
            "Submit the permit application, biometrics and medical documents if required; wait for the official decision before travel."
        ],
        "sections": {
            "overview": section("Overview", overview),
            "apply": section("Application process", apply),
            "eng": section("English and study gap", eng),
            "money": section("Tuition and living costs", money),
            "visa": section("Student visa / residence permit", visa),
            "after": section("Work during and after study", after),
            "schol": section("Scholarships", schol)
        }
    }
    return meta, facts, {"source": "https://www.wikidata.org/", "ranking_note": "Ranks are added only from data/rankings.json.", "universities": unis}, content

if __name__ == "__main__":
    if len(sys.argv) != 2 or len(sys.argv[1]) != 2 or not sys.argv[1].isalpha():
        sys.exit("Usage: python scripts/add_country.py <ISO-3166 alpha-2 code>")
    cc = sys.argv[1].strip().lower()
    meta, facts, unis, content = build(cc)
    for key, obj in (("facts", facts), ("universities", unis), ("content", content)):
        save("data/%s/%s.json" % (cc, key), obj)
    countries = [x for x in load("data/countries.json", []) if x["code"] != cc]
    countries.append({"code": cc, "name": meta["name"], "flag": meta["flag"], "dir": cc, "currency": meta["currency"]})
    countries.sort(key=lambda x: x["name"].casefold())
    save("data/countries.json", countries)
    print("Generated %s (%s): %d university directory records." % (meta["name"], cc.upper(), len(unis["universities"])))
