
/* app-ext.js: ranking providers and Add country dialog.
   Loaded after app.js and before the app boots. */
(function () {
  var SUB = "Bangladesh applicants · Universities, rankings, application, visa and money.";
  var LOADING = false;
  var RK = { providers: {}, ranks: {} };
  var PROV = "qs";
  var CUS = {};
  var CL = [];
  var PICK = null;

  try {
    PROV = localStorage.getItem("prov") || "qs";
    CUS = JSON.parse(localStorage.getItem("custom-countries") || "{}");
    if (!CUS || typeof CUS !== "object") CUS = {};
  } catch (e) {}

  var save = function () {
    try {
      localStorage.setItem("custom-countries", JSON.stringify(CUS));
    } catch (e) {}
  };

  function norm(s) {
    return String(s || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/\(.*?\)/g, "")
      .replace(/^the /, "")
      .replace(/[^a-z0-9]+/g, " ")
      .trim();
  }

  /* ---------- ranking providers ---------- */

  var RP = (
    window.__DATA__ && window.__DATA__.rankings
      ? Promise.resolve(window.__DATA__.rankings)
      : fetch("data/rankings.json", { cache: "no-cache" })
          .then(function (r) {
            if (!r.ok) throw new Error("Rankings unavailable");
            return r.json();
          })
  )
    .then(function (j) {
      RK = j || { providers: {}, ranks: {} };
      RK.providers = RK.providers || {};
      RK.ranks = RK.ranks || {};

      if (!RK.providers[PROV]) {
        PROV = Object.keys(RK.providers)[0] || "qs";
      }
    })
    .catch(function () {
      RK = { providers: {}, ranks: {} };
    });

  function decorate(d) {
    if (!d || !d.content || !d.content.meta || !d.universities) return d;

    d.content.meta.sub = SUB;

    var tbl = RK.ranks[PROV] || {};
    var P = RK.providers[PROV];

    if (!P) return d;

    var L = d.universities.universities || [];
    var m = d.content.meta;
    var list = [];

    L.forEach(function (u) {
      var r = tbl[norm(u.name)];

      u.rk = r || null;
      u.top10 = false;

      delete u.top10_rank;
      delete u.rank_label;

      if (r && r.n != null) {
        u.top10 = true;
        list.push(u);
      }
    });

    list.sort(function (a, b) {
      return a.rk.n - b.rk.n || a.name.localeCompare(b.name);
    });

    list.forEach(function (u, i) {
      u.top10_rank = i + 1;
      u.rank_label = P.short + " " + P.edition + " · #" + u.rk.r;
    });

    m.top_label = P.short + " ranked";

    m.rank_note =
      P.name + " " + P.edition + ": " +
      list.length + " of " + L.length +
      " listed institutions have a rank in the data. " +
      "The rest sit under Others, together with institutions this provider does not rank.";

    return d;
  }

  var _load = load;

  load = function (c) {
    return (
      CUS[c] && !CC.some(function (entry) { return entry.code === c; })
        ? Promise.resolve(CUS[c])
        : _load(c)
    ).then(function (d) {
      return RP.then(function () {
        decorate(d);
        return d;
      });
    });
  };

  var _uh = unisHtml;

  unisHtml = function () {
    var ks = Object.keys(RK.providers);
    var h = _uh();

    if (!ks.length) return h;

    var seg =
      '<div class="seg prov" id="prov" role="group" aria-label="Ranking provider">' +
      ks.map(function (k) {
        return (
          '<button data-p="' + esc(k) +
          '" aria-pressed="' + (k == PROV) + '">' +
          esc(RK.providers[k].short) +
          "</button>"
        );
      }).join("") +
      '</div><p class="pnote" id="pnote"></p>';

    return h.replace('<div class="stats">', seg + '<div class="stats">');
  };

  var _wu = wireUnis;

  wireUnis = function () {
    _wu();

    var P = RK.providers[PROV];
    if (!P) return;

    var scopeButtons = qa("#scope button");

    if (scopeButtons.length) {
      scopeButtons[0].textContent = META.top_label;
    }

    var s1 = $("#s1");
    if (s1 && s1.nextElementSibling) {
      s1.nextElementSibling.textContent = META.top_label;
    }

    qa("#prov button").forEach(function (b) {
      b.setAttribute("aria-pressed", b.dataset.p == PROV);

      b.onclick = function () {
        PROV = b.dataset.p;

        try {
          localStorage.setItem("prov", PROV);
        } catch (e) {}

        decorate(D);
        wireUnis();
      };
    });

    if (!D.universities.universities.some(function (u) {
      return u.top10;
    })) {
      var rb = $("#scope button[data-s=rest]");
      if (rb) rb.click();
    }

    var pn = $("#pnote");

    if (pn) {
      pn.innerHTML =
        esc(P.name + " " + P.edition) +
        " · data checked " + esc(RK.updated || "") +
        ' · <a href="' + esc(P.url) +
        '" target="_blank" rel="noopener">official table</a>';
    }
  };

  var _card = card;

  card = function (u) {
    var h = _card(u);
    var P = RK.providers[PROV];
    var r = u.rk;
    var t;

    if (!P) return h;

    if (r) {
      t =
        (r.n != null
          ? "<b>" + esc(P.short + " " + P.edition) +
            "</b>: " + esc(r.r)
          : "") +
        (r.note ? " " + esc(r.note) : "") +
        (r.src
          ? ' · <a href="' + esc(r.src) +
            '" target="_blank" rel="noopener">source</a>'
          : "");
    } else {
      t = esc(P.short + " " + P.edition) +
        ": no rank in the current data.";
    }

    return h.replace(
      "</dl>",
      '</dl><p class="src">' + t + "</p>"
    );
  };


})();
