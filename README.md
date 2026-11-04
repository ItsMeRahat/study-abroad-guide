# Study Abroad Guide

A static, no-build web guide for Bangladesh applicants: universities, application steps, money, permits and scholarships, now with a **ranking-provider switch (QS / THE)** and an **Add country** feature.

## Run it
- **GitHub Pages:** push the repo, then Settings > Pages > deploy from the `main` branch root. `index.html` loads everything from `data/`.
- **Locally:** `python -m http.server`, then open http://localhost:8000. Or open `standalone.html` directly (all data embedded).

## Features
- **Ranking provider:** the Universities tab has a QS / THE switch. Ranked institutions are sorted by that provider's rank, the rest sit under *Others*; every rank shows its source link. Add providers by extending `data/rankings.json` (`providers` + `ranks`).
- **Add country (in the browser):** `+ Add country` pulls the profile (REST Countries), BDT exchange rate (open.er-api.com) and universities with an official website (Wikidata), then matches QS/THE ranks by name. Saved in that browser's localStorage; remove from the same dialog.
- **Add country (in the repo):** `python scripts/add_country.py DK` writes `data/dk/*.json` and registers the country, so it ships with the site.
- **Rankings:** `python scripts/update_rankings.py qs 2027 <csv|json-url|file>` (same for `the`) imports a ranking table into `data/rankings.json`.
- **Exchange rates:** `scripts/update_rate.py`; `.github/workflows/refresh.yml` runs it monthly and rebuilds `standalone.html`.
- After any data change run `python scripts/build_standalone.py`.

## Data and its limits
- `data/rankings.json` is seeded only with ranks I could confirm from published sources (QS 2027: Lund, KTH, Uppsala, Stockholm, the eight Norwegian entries; THE 2027: Karolinska, Lund, KTH, Uppsala, Gothenburg, Oslo). Uppsala's QS rank is flagged: its own site says 87, QS's top-100 page shows =90. All other institutions show "no rank in the current data" until you import a full table.
- Auto-added countries get profile, exchange rate, universities and ranks only. Tuition, visa rules, deadlines and scholarships are programme- and year-specific, so they are never auto-filled; the page says to confirm them officially.
- Wikidata lists are only as complete as Wikidata; browser fetching needs network access to restcountries.com, query.wikidata.org and open.er-api.com.
- `update_rankings.py` and `add_country.py` call live sites and were only tested against stubbed responses; check their output before committing.

## Layout
`index.html` `style.css` `app.js` (guide logic) `app-ext.js` (rankings + add country) · `data/` (`countries.json`, `rankings.json`, one folder per country; Sweden is the root `facts/universities/content.json`) · `scripts/` · `standalone.html` (generated).
