# Study Abroad Guide

A static, no-build web guide for Bangladesh applicants: universities, application steps, money, permits and scholarships, now with a **ranking-provider switch (QS / THE)** and an **Add country** feature.

## Run it
- **GitHub Pages:** push the repo, then Settings > Pages > deploy from the `main` branch root. `index.html` loads everything from `data/`.
- **Locally:** `python -m http.server`, then open http://localhost:8000. Or open `standalone.html` directly (all data embedded).

## Features
- **Country guides:** Sweden and Norway are maintained country guides. Each country has its own `data/<code>/facts.json`, `universities.json`, and `content.json` files.
- **Add country (temporary preview):** `+ Add country` can build a browser-only preview. It is stored in that browser and is not published to other visitors.
- **Add country (permanent, owner only):** choose a country and select **Request permanent country data**. This opens a prefilled GitHub issue. The repository owner must create the issue while signed in as `ItsMeRahat`; the `Generate country data` GitHub Actions workflow then creates the country JSON files, registers the country and rebuilds `standalone.html`. GitHub Pages deploys the commit.
- **Generated data and verification:** country profile, currency and a university directory are collected from public datasets. Admission rules, Bangladesh credential equivalency, English/MOI waivers, tuition, proof of funds, immigration rules, work rights, post-study routes and scholarships must be sourced from official government/university pages. Until verified, the guide explicitly marks them as needing verification; it does not invent a score, fee or policy.
- **Ranking provider:** the Universities tab has a QS / THE switch. Only entries present in `data/rankings.json` receive a rank. An absent rank is not inferred.
- **Exchange rates:** `scripts/update_rate.py`; `.github/workflows/refresh.yml` runs it monthly and rebuilds `standalone.html`.
- **Local generator:** `python scripts/add_country.py CA` generates a country data scaffold from public sources. Run `python scripts/build_standalone.py` after data changes.
- **Public use:** visitors can browse published countries without signing in. Only the repository owner can publish a new permanent country to the shared site.

## Layout
`index.html` `style.css` `app.js` (guide logic) `app-ext.js` (rankings + add country) · `data/` (`countries.json`, `rankings.json`, one folder per country; Sweden is the root `facts/universities/content.json`) · `scripts/` · `standalone.html` (generated).
