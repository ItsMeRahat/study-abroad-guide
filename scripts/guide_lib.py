"""Shared helpers: name normalisation (identical to app-ext.js), JSON I/O, HTTP."""
import json, re, unicodedata, urllib.request, urllib.parse, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
UA = {"User-Agent": "study-abroad-guide/1.0 (personal project)"}

def norm(s):
    s = unicodedata.normalize("NFD", str(s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"^the ", "", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()

def rank_num(r):
    m = re.search(r"\d+", str(r))
    return int(m.group()) if m else None

def today():
    return datetime.date.today().isoformat()

def load(path, default=None):
    p = ROOT / path
    return json.loads(p.read_text(encoding="utf8")) if p.exists() else default

def save(path, obj):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf8")

def get(url, params=None, timeout=60):
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read().decode("utf8")

def get_json(url, params=None):
    return json.loads(get(url, params))

def fx_to_bdt(cur):
    try:
        r = get_json("https://open.er-api.com/v6/latest/" + cur)["rates"]["BDT"]
        if r > 0:
            return float(r)
    except Exception:
        pass
    j = get_json("https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/%s.json" % cur.lower())
    return float(j[cur.lower()]["bdt"])
