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
    population = c.get("population") or None
    population_year = None
    if not population:
        population, population_year = world_bank_population(cc)
    unis, uni_source = universities(cc)

    facts = {
        "last_checked": today(),
        "data_status": "needs_official_verification",
        "population": population,
        "population_year": population_year,
        "population_source": "https://api.worldbank.org/v2/country/%s/indicator/SP.POP.TOTL" % cc.upper(),
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
    apply = '<p>Use this preparation checklist for ' + html.escape(name) + '. Confirm every requirement and deadline with the institution and official immigration authority.</p><div class="bar"><i id="pb"></i></div><ol class="steps" id="st"></ol><h3>Before paying an application fee</h3><ul><li>Confirm the institution is recognised and authorised to enrol international students.</li><li>Record the exact programme intake, deadline, academic prerequisites, tuition, extra fees and refund policy.</li><li>Ask admissions to assess your Bangladesh HSC or bachelor’s qualification in writing.</li><li>Confirm accepted English tests, overall and component scores, validity period and any MOI waiver policy.</li><li>Save the official offer, fee schedule and all correspondence.</li></ul><div class="note warn">The national application portal and deadlines are not verified for this country. Use the institution’s own portal until an official national route is confirmed.</div>'
    eng = '<details open><summary>English language tests</summary><div><p>IELTS Academic, TOEFL iBT, PTE Academic, Duolingo English Test and other tests are not universally accepted. Each institution/programme sets accepted tests, minimum overall and component scores, validity and exemption rules. Do not assume an MOI waiver; obtain written confirmation.</p></div></details><details><summary>Bangladesh qualification and study gap</summary><div><p>Ask admissions to assess your exact board, HSC subjects, grades, passing year or bachelor’s degree, duration and grading scale. There may be no single national study-gap limit; the institution and immigration authority may assess reasons and evidence individually. Explain gaps honestly and provide dated employment or training evidence where relevant.</p></div></details><div class="note">No country-wide IELTS score, MOI waiver or study-gap rule is published unless supported by a current official source.</div>'
    money = '<details open><summary>Tuition and mandatory fees</summary><div><p>Compare tuition for the exact programme, degree level, credit load and intake. Add application, enrolment, student-service, laboratory, placement, insurance and other compulsory charges. Ask whether fees can rise each year.</p></div></details><details><summary>Living and arrival budget</summary><div><p>Estimate accommodation, utilities, food, local transport, phone/internet, books, clothing, health insurance and initial setup costs for the city where you will study. Costs differ by city and household size.</p></div></details><div class="card"><h3>Budget conversion</h3><label for="mo">Number of months</label><input id="mo" type="number" min="1" max="48" value="12"><p id="tot">Living-cost estimate: Needs verification</p><p id="bdt">BDT conversion will use the available exchange rate.</p><small id="fxn">Exchange rate is indicative and may change.</small></div><div class="note warn">Do not treat part-time work as proof of funds. Verify the official minimum, accepted evidence, family-member amounts and currency rules. Tuition and travel may be additional.</div>'
    visa = '<h3>Study visa / residence permit checklist</h3><ol><li>Confirm the correct permit category for your course length, institution and nationality.</li><li>Check whether an admission letter or government attestation is required.</li><li>Read the official checklist for passport validity, photographs, forms, fees and translations.</li><li>Prepare tuition/living-fund evidence, source of funds and sponsor documents if required.</li><li>Check biometrics, medical examination, police certificate and interview requirements for Bangladesh applicants.</li><li>Apply through the official government portal and save submission/payment receipts.</li><li>Use the official processing-time tool and avoid non-refundable travel before approval.</li></ol><div class="note warn">Permit category, fee, financial threshold, biometrics route and processing time must be verified from the official immigration authority.</div>'
    after = '<details open><summary>Work during study</summary><div><p>Check whether student status permits on-campus/off-campus work, weekly limits during term, rules during scheduled breaks, internship/co-op authorisation and restrictions for language or preparatory courses. Do not assume all students may work.</p></div></details><details><summary>After graduation</summary><div><p>Check whether the exact qualification and institution can lead to a post-study work permit. Verify programme duration, application deadline, language or field-of-study conditions, permit length and any longer-term residence route. Admission alone never guarantees a work permit or permanent residence.</p></div></details><div class="note warn">No work-hour limit or post-study route is stated as fact until confirmed on the official government source.</div>'
    schol = '<h3>Where to look</h3><ul><li>Government-funded scholarships and bilateral education programmes.</li><li>University entrance awards and merit scholarships for international students.</li><li>Departmental funding, research assistantships and supervisor-funded positions for postgraduate applicants.</li><li>External foundations and professional organisations related to your subject.</li></ul><h3>Check every award carefully</h3><p>Confirm eligibility for Bangladeshi applicants, degree level, academic conditions, separate application, deadlines, renewal criteria and whether the award covers tuition, living costs, insurance or travel. Never pay anyone who guarantees an award.</p><div class="note warn">Country-specific scholarship names and current deadlines are added only after checking the official provider’s active call.</div>'
    meta = {
        "code": cc, "name": name, "flag": flag_emoji(cc), "currency": cur,
        "title": "Study in " + name + ": Applicant Guide",
        "sub": "Bangladesh applicants · Universities, admission, costs, visa and scholarships.",
        "portal": "University directory", "portal_url": "https://www.wikidata.org/",
        "top_label": "QS/THE ranked", "uni_title": name + " universities",
        "prog_btn": "Official university website",
        "list_note": "Public-data directory candidates may include colleges or affiliated institutions and may be incomplete. Confirm recognition and programme eligibility on official government and institution lists.",
        "rank_note": "Only ranks present in the maintained QS/THE dataset are displayed. No rank is inferred.",
        "gen_note": "University directory data is automatically collected. Confirm every programme, fee and entry requirement on the official university website.",
        "caution": "<b>Country guide · research status:</b> this guide contains a practical preparation framework and public institution directory. Country-specific admissions, tuition, financial thresholds, immigration, work rights and scholarships are published as confirmed facts only after official-source review. Verify all current rules before applying."
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
    if cc == "ca":
        facts.update({
            "data_status": "official_sources_added_review_institution_specific",
            "maintenance": {"monthly": 1954, "annual": 23448, "source": "IRCC financial support requirement; applies from 2026-09-01 outside Quebec, excluding tuition and travel."},
            "work_hours_per_week": 24,
            "fees": {"international_undergraduate_average": 41746, "international_graduate_average": 24028, "academic_year": "2025/2026", "source": "Statistics Canada"},
            "links": {
                "study_permit": "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/study-permit/apply.html",
                "dli_list": "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/study-permit/prepare/designated-learning-institutions-list.html",
                "funds": "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/study-permit/get-documents/financial-support.html",
                "pal_tal": "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/study-permit/get-documents/provincial-attestation-letter.html",
                "work": "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/work/work-off-campus.html",
                "pgwp": "https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/work/after-graduation/eligibility.html",
                "scholarships": "https://www.educanada.ca/scholarships-bourses/searchAll-rechercheTous.aspx?lang=eng"
            }
        })
        content["meta"].update({
            "portal": "EduCanada · Government of Canada",
            "portal_url": "https://www.educanada.ca/",
            "caution": "<b>Canada guide · checked 2026-11-04:</b> government policy links are provided below. Tuition, admission, English scores, study-gap decisions and scholarship awards vary by institution/programme. Recheck IRCC and university pages before applying."
        })
        content["sections"]["apply"] = section("Application process", """<ol>
<li>Choose a programme and intake; compare entry prerequisites, total tuition, campus and co-op structure.</li>
<li>Check that the institution is on IRCC’s <a href="https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/study-permit/prepare/designated-learning-institutions-list.html" target="_blank" rel="noopener">Designated Learning Institution (DLI) list</a>. Confirm the exact programme is PGWP-eligible separately if that matters to your plan.</li>
<li>Read the university’s Bangladesh-specific entry requirements. For undergraduate admission, ask how it assesses HSC subjects and grades; for graduate admission, confirm bachelor’s degree length, discipline and GPA conversion.</li>
<li>Meet the programme’s English-language requirement and submit any required test score. Accepted tests, minimum scores and possible waivers are institution- and programme-specific.</li>
<li>Submit the university application with transcripts, certificates, passport, references, statement of purpose, CV/portfolio and translations where required.</li>
<li>Review the written offer, tuition deposit, refund/deferment policy and any conditions. Ask the institution to issue and validate the Letter of Acceptance (LOA).</li>
<li>Check whether a PAL/TAL or Quebec CAQ is required for your case. Do not assume an exemption; follow the current IRCC decision guide.</li>
<li>Prepare proof of funds, study plan and supporting documents, then submit the study permit application online. Complete biometrics/medical steps if requested.</li>
</ol><p><b>Timing:</b> IRCC recommends applying well before the programme begins. University deadlines differ by institution, programme and intake; there is no single national deadline.</p><p class="links"><a href="https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/study-permit/apply.html" target="_blank" rel="noopener">Official study permit application guide</a> · <a href="https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/study-permit/get-documents.html" target="_blank" rel="noopener">Required documents</a></p>""")
        content["sections"]["eng"] = section("English and Bangladesh study-gap guidance", """<h3>English proficiency</h3><p>There is no single IELTS/TOEFL score that applies to every Canadian institution. Each university and programme sets its accepted tests, minimum overall score, component scores and test-validity period. Confirm the exact rule on the programme page before booking a test.</p><p>An MOI (Medium of Instruction) letter is not a nationwide automatic IELTS waiver. Some institutions or programmes may consider it under their own policy; obtain written confirmation from admissions.</p><h3>Bangladesh qualifications and study gap</h3><p>HSC subject prerequisites, grade conversion, foundation/pathway requirements and bachelor’s degree equivalency are assessed by the receiving institution. Canada has no single universal study-gap limit for all universities. Explain any gap honestly with dated employment, training, caregiving or other supporting evidence where relevant; the institution and visa officer assess the complete case.</p><p><b>Action:</b> email international admissions with your exact board, qualification, passing year, subjects, grades and intended programme, and request a written assessment.</p>""")
        content["sections"]["money"] = section("Tuition, living costs and budget", """<h3>Published national tuition averages (2025/2026)</h3><p>Statistics Canada reported average international tuition of <b>CAD 41,746/year for undergraduate</b> and <b>CAD 24,028/year for graduate</b> students. These are national averages, not an offer or a price quote; actual fees vary substantially by province, institution and programme.</p><p><a href="https://www150.statcan.gc.ca/n1/daily-quotidien/250910/dq250910d-eng.htm" target="_blank" rel="noopener">Statistics Canada: Tuition in Canada, 2025/2026</a></p><h3>IRCC living-funds minimum</h3><p>For study-permit applications made on or after <b>1 September 2026</b>, a single applicant studying outside Quebec must show <b>CAD 23,448</b> for one year of living expenses, in addition to first-year tuition and transportation. The required amount changes with family size and Quebec has separate rules. This is an immigration minimum, not a realistic full budget for every city.</p><p><a href="https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/study-permit/get-documents/financial-support.html" target="_blank" rel="noopener">IRCC proof of financial support and family-size table</a></p><div class="card"><h3>Living-funds conversion (outside Quebec, one applicant)</h3><p>CAD 23,448 per year · CAD 1,954 per month (simple 12-month equivalent). Tuition and travel are additional.</p><label for="mo">Number of months</label><input id="mo" type="number" min="1" max="12" value="12"><p id="tot">CAD 23,448</p><p id="bdt">BDT estimate uses the indicative exchange rate.</p><small id="fxn">Bank rates and transfer costs differ.</small></div><p>IRCC expects funds for the first year and a credible plan for the remaining study period. Do not rely on expected part-time work to meet the proof-of-funds requirement.</p>""")
        content["sections"]["visa"] = section("Canada study permit", """<ol><li>Obtain a valid Letter of Acceptance from a DLI.</li><li>Check the current PAL/TAL requirement. From 1 January 2026, certain master’s and doctoral students at public DLIs are exempt; other categories and exceptions have separate rules. Quebec applicants may need a CAQ.</li><li>Prepare proof of tuition payment/tuition funds, living expenses, travel costs and the source/accessibility of funds.</li><li>Prepare passport, LOA, required attestation/CAQ, study plan/letter of explanation and any country-specific checklist documents.</li><li>Apply online, pay the applicable fees and complete biometrics and medical examination if requested.</li><li>Wait for the decision and follow the letter/port-of-entry instructions. A study permit is not itself a visa or eTA for travel.</li></ol><p>Approval is not guaranteed. Processing time varies and should be checked using IRCC’s live tool; no fixed processing duration is promised here.</p><p class="links"><a href="https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/study-permit/apply.html" target="_blank" rel="noopener">Apply for a study permit</a> · <a href="https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/study-permit/get-documents/provincial-attestation-letter.html" target="_blank" rel="noopener">PAL/TAL rules</a> · <a href="https://www.canada.ca/en/immigration-refugees-citizenship/services/application/check-processing-times.html" target="_blank" rel="noopener">Check processing times</a></p>""")
        content["sections"]["after"] = section("Work during study and after graduation", """<h3>Work while studying</h3><p>Eligible international students may work off campus up to <b>24 hours per week</b> during regular academic sessions. During regularly scheduled breaks, eligible students may work unlimited hours. You must meet all study-permit conditions; some students/programmes are not eligible. Working more than the permitted limit can affect status.</p><p><a href="https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/work/work-off-campus.html" target="_blank" rel="noopener">IRCC: Work off campus as an international student</a></p><h3>Post-Graduation Work Permit (PGWP)</h3><p>Graduation from a DLI does not automatically make a student PGWP-eligible. The exact institution and programme must qualify. General requirements include an eligible programme of at least 8 months (Quebec programme rules can differ), maintaining required full-time status, and applying within 180 days of confirmation of completion.</p><p>Many applicants must also meet language requirements; eligible non-degree programmes may have field-of-study rules. Requirements depend on credential type and the date of the study-permit application. Check the current IRCC eligibility page before choosing a programme or relying on a post-study work route.</p><p><a href="https://www.canada.ca/en/immigration-refugees-citizenship/services/study-canada/work/after-graduation/eligibility.html" target="_blank" rel="noopener">IRCC: PGWP eligibility</a></p>""")
        content["sections"]["schol"] = section("Scholarships and funding", """<p>Search the official Government of Canada EduCanada scholarship database and each university’s own international-student awards page. Funding may be merit-based, need-based, programme-specific or research-supervisor-funded. Eligibility, country restrictions, award value and deadlines differ; many awards require a separate application.</p><ul><li>Check entrance scholarships automatically considered with admission and awards requiring a separate form.</li><li>For research master’s/PhD programmes, contact prospective supervisors and departments about assistantships, grants and funded positions.</li><li>Confirm whether an award covers tuition only or also living costs, travel and insurance.</li><li>Never pay an agent or third party to “guarantee” a scholarship or visa.</li></ul><p><a href="https://www.educanada.ca/scholarships-bourses/searchAll-rechercheTous.aspx?lang=eng" target="_blank" rel="noopener">EduCanada official scholarship search</a> · <a href="https://www.educanada.ca/scholarships-bourses/index.aspx?lang=eng" target="_blank" rel="noopener">International scholarships overview</a></p>""")
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
