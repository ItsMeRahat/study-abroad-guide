"""Build standalone.html (everything embedded, opens from a file or any host) from index.html + data/."""
import json, re
from guide_lib import ROOT, load

countries = load("data/countries.json")
data = {"countries": countries, "rankings": load("data/rankings.json", {}), "c": {}}
for c in countries:
    d = "data/" + (c["dir"] + "/" if c.get("dir") else "")
    data["c"][c["code"]] = {k: load(d + k + ".json") for k in ("facts", "universities", "content")}
safe = lambda s: re.sub(r"</(script)", r"<\\/\1", s, flags=re.I)  # only the sequence that would end the tag
html = (ROOT / "index.html").read_text(encoding="utf8")
html = re.sub(r'<link rel="stylesheet" href="style\.css(?:\?[^"]*)?">', lambda m: "<style>" + (ROOT / "style.css").read_text(encoding="utf8") + "</style>", html)
js = "window.__DATA__=" + safe(json.dumps(data, ensure_ascii=False)) + ";\n" + (ROOT / "app.js").read_text(encoding="utf8") + "\n" + (ROOT / "app-ext.js").read_text(encoding="utf8")
html = re.sub(r'<script src="app\.js(?:\?[^" ]*)?"></script>\s*<script src="app-ext\.js(?:\?[^" ]*)?"></script>', lambda m: "<script>" + safe(js) + "</script>", html)
(ROOT / "standalone.html").write_text(html, encoding="utf8")
print("standalone.html written,", len(html) // 1024, "KB")
