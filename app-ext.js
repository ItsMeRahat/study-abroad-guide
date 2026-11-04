
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
      CUS[c]
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

    var scopeButtons = $$("#scope button");

    if (scopeButtons.length) {
      scopeButtons[0].textContent = META.top_label;
    }

    var s1 = $("#s1");
    if (s1 && s1.nextElementSibling) {
      s1.nextElementSibling.textContent = META.top_label;
    }

    $$("#prov button").forEach(function (b) {
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

  /* ---------- add country ---------- */

  var _boot = boot;

  boot = function (cs) {
    return _boot(
      cs.concat(
        Object.keys(CUS).map(function (k) {
          return CUS[k].entry;
        })
      )
    );
  };

  function refreshSel() {
    $("#cc").innerHTML = CC.map(function (x) {
      return (
        '<option value="' + esc(x.code) + '">' +
        esc(x.flag + " " + x.name) +
        "</option>"
      );
    }).join("");

    $("#cc").value = code;
  }

  var host = $(".cs");

  host.insertAdjacentHTML(
    "beforeend",
    '<button class="ghost" id="addc" type="button" aria-label="Add a country">+ Add country</button>'
  );

  document.body.insertAdjacentHTML(
    "beforeend",
    '<dialog id="dlg" aria-labelledby="dt">' +
      '<div class="dl">' +
        '<h2 id="dt">Add a country</h2>' +
        "<p>Pick a country and the guide builds its page from original sources: profile, exchange rate to BDT, universities with an official website and QS/THE ranks from the bundled ranking data.</p>" +
        '<input type="search" id="cq" placeholder="Search countries" aria-label="Search countries">' +
        '<div id="clist" role="listbox"></div>' +
        '<p id="cpick"></p>' +
        '<ol id="clog"></ol>' +
        '<div class="acts">' +
          '<button class="btn sm" id="cgo" disabled>Fetch and add</button>' +
          '<button class="btn alt sm" id="cx">Close</button>' +
        '</div>' +
        '<div id="cadded"></div>' +
      '</div>' +
    '</dialog>'
  );

  var dlg = $("#dlg");

  $("#addc").onclick = function () {
    dlg.showModal();

    if (!CL.length) loadList();

    added();
  };

  $("#cx").onclick = function () {
    dlg.close();
  };

  $("#cq").oninput = filter;

  function netfail() {
    return (
      '<div class="note warn">' +
      '<b>Country data could not be loaded.</b> ' +
      'Please check your internet connection and try again. ' +
      'If the problem continues, the data service may be temporarily unavailable.' +
      "</div>"
    );
  }

  /* Public country dataset; replaces deprecated REST Countries v3.1 */

  function loadList() {
    LOADING = true;
    $("#clist").textContent = "Loading countries...";

    return fetch(
      "https://cdn.jsdelivr.net/gh/mledoze/countries@master/countries.json",
      { cache: "no-cache" }
    )
      .then(function (r) {
        if (!r.ok) {
          throw new Error("Country data request failed");
        }

        return r.json();
      })
      .then(function (a) {
        if (!Array.isArray(a)) {
          throw new Error("Invalid country data");
        }

        CL = a.map(function (c) {
          return {
            name: c.name || {},
            cca2: c.cca2 || "",
            flag: c.flag || "",
            currencies: c.currencies || {},
            capital: c.capital || [],
            region: c.region || "",
            subregion: c.subregion || "",
            population: c.population || 0,
            languages: c.languages || {}
          };
        }).filter(function (c) {
          return c.name.common && c.cca2;
        });

        CL.sort(function (x, y) {
          return x.name.common.localeCompare(y.name.common);
        });

        LOADING = false;
        filter();
      })
      .catch(function () {
        LOADING = false;
        $("#clist").innerHTML = netfail();
      });
  }

  function filter() {
    if (!CL.length) {
      $("#clist").innerHTML = LOADING
        ? "Loading countries..."
        : netfail();

      return;
    }

    var q = norm($("#cq").value);
    var have = CC.map(function (x) {
      return x.code.toLowerCase();
    });

    var L = CL.filter(function (c) {
      return (
        have.indexOf(c.cca2.toLowerCase()) < 0 &&
        (!q || norm(c.name.common).indexOf(q) > -1)
      );
    }).slice(0, 80);

    $("#clist").innerHTML = L.length
      ? L.map(function (c) {
          return (
            '<button type="button" role="option" data-c="' +
            esc(c.cca2) +
            '" aria-pressed="' +
            (PICK && PICK.cca2 == c.cca2) +
            '">' +
            esc(c.flag + " " + c.name.common) +
            "</button>"
          );
        }).join("")
      : '<div class="note">No match, or already added.</div>';

    $$("#clist button").forEach(function (b) {
      b.onclick = function () {
        PICK = CL.filter(function (c) {
          return c.cca2 == b.dataset.c;
        })[0];

        if (!PICK) return;

        var cur = Object.keys(PICK.currencies || {})[0] || "USD";

        $("#cpick").textContent =
          PICK.flag + " " + PICK.name.common +
          " · currency " + cur +
          " · capital " + (PICK.capital || ["n/a"]).join(", ");

        $("#cgo").disabled = false;

        filter();
      };
    });
  }

  function added() {
    var ks = Object.keys(CUS);

    $("#cadded").innerHTML = ks.length
      ? "<p>Added in this browser</p>" +
        ks.map(function (k) {
          return (
            '<div class="added">' +
            '<span>' +
            esc(CUS[k].entry.flag + " " + CUS[k].entry.name) +
            "</span>" +
            '<button class="ghost" data-r="' + esc(k) +
            '">Remove</button>' +
            "</div>"
          );
        }).join("")
      : "";

    $$("#cadded [data-r]").forEach(function (b) {
      b.onclick = function () {
        var k = b.dataset.r;

        delete CUS[k];
        save();

        CC = CC.filter(function (x) {
          return x.code != k;
        });

        if (code == k && CC.length) {
          code = CC[0].code;
          refreshSel();
          setCountry(code, "overview");
        } else {
          refreshSel();
        }

        added();
        filter();
      };
    });
  }

  function step(i, cls, msg) {
    var li = $("#clog").children[i];

    if (!li) return;

    li.className = cls;

    li.textContent =
      (cls == "ok" ? "Done: " :
       cls == "er" ? "Failed: " :
       "Working: ") + msg;
  }

  /* ---------- exchange rate ---------- */

  function fx(cur) {
    return fetch(
      "https://open.er-api.com/v6/latest/" + encodeURIComponent(cur)
    )
      .then(function (r) {
        if (!r.ok) throw new Error("Exchange rate unavailable");
        return r.json();
      })
      .then(function (j) {
        if (j.rates && j.rates.BDT > 0) {
          return j.rates.BDT;
        }

        throw new Error("BDT rate unavailable");
      })
      .catch(function () {
        return fetch(
          "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/" +
          cur.toLowerCase() + ".json"
        )
          .then(function (r) {
            if (!r.ok) throw new Error("Backup rate unavailable");
            return r.json();
          })
          .then(function (j) {
            var rate = j[cur.toLowerCase()] &&
              j[cur.toLowerCase()].bdt;

            if (!(rate > 0)) {
              throw new Error("BDT rate unavailable");
            }

            return rate;
          });
      });
  }

  /* ---------- Wikidata universities ---------- */

  function unis(cc) {
    var q =
      'SELECT ?u (SAMPLE(?l) AS ?n) (SAMPLE(?w) AS ?web) (SAMPLE(?cl) AS ?city) WHERE { ' +
      '?c wdt:P297 "' + cc + '". ' +
      '?u wdt:P31/wdt:P279* wd:Q3918; wdt:P17 ?c; wdt:P856 ?w; rdfs:label ?l. ' +
      'FILTER(LANG(?l)="en") ' +
      'FILTER NOT EXISTS { ?u wdt:P576 ?x } ' +
      'OPTIONAL { ?u wdt:P131 ?ci. ?ci rdfs:label ?cl. FILTER(LANG(?cl)="en") } ' +
      '} GROUP BY ?u LIMIT 400';

    function request(endpoint) {
      var controller =
        typeof AbortController !== "undefined"
          ? new AbortController()
          : null;

      var timer = controller
        ? setTimeout(function () {
            controller.abort();
          }, 25000)
        : null;

      return fetch(
        endpoint +
          (endpoint.indexOf("?") >= 0 ? "&" : "?") +
          "format=json&query=" + encodeURIComponent(q),
        {
          headers: {
            Accept: "application/sparql-results+json"
          },
          signal: controller ? controller.signal : undefined
        }
      )
        .then(function (r) {
          if (!r.ok) throw new Error("University source unavailable");
          return r.json();
        })
        .then(function (j) {
          var bindings =
            j.results && j.results.bindings
              ? j.results.bindings
              : [];

          var seen = {};
          var out = [];

          bindings.forEach(function (b) {
            if (!b.n || !b.n.value || !b.web || !b.web.value) return;

            var n = b.n.value;
            var k = norm(n);

            if (/^Q\\d+$/.test(n) || seen[k]) return;

            seen[k] = 1;

            out.push({
              id: k.replace(/ /g, "-"),
              name: n,
              city: b.city ? b.city.value : "See website",
              website: b.web.value,
              top10: false
            });
          });

          return out.sort(function (a, b) {
            return a.name.localeCompare(b.name);
          });
        })
        .then(
          function (result) {
            if (timer) clearTimeout(timer);
            return result;
          },
          function (error) {
            if (timer) clearTimeout(timer);
            throw error;
          }
        );
    }

    return request("https://qlever.dev/api/wikidata")
      .catch(function () {
        return request("https://query.wikidata.org/sparql");
      })
      .catch(function () {
        var empty = [];
        empty.unavailable = true;
        return empty;
      });
  }

  /* ---------- fetch and add ---------- */

  $("#cgo").onclick = function () {
    if (!PICK) return;

    var c = PICK;
    var cc = c.cca2.toLowerCase();
    var name = c.name.common;
    var cur = Object.keys(c.currencies || {})[0] || "USD";
    var day = new Date().toISOString().slice(0, 10);

    $("#cgo").disabled = true;

    $("#clog").innerHTML = [
      "Country profile",
      "Exchange rate to BDT",
      "Universities from Wikidata",
      "QS and THE ranks"
    ].map(function () {
      return "<li></li>";
    }).join("");

    step(
      0,
      "ok",
      name + ", " + (c.capital || ["n/a"]).join(", ")
    );

    step(1, "", "contacting exchange rate service");
    step(2, "", "querying Wikidata");

    RP.then(function () {
      return Promise.all([
        fx(cur).then(function (r) {
          step(
            1,
            "ok",
            "1 " + cur + " = " + (+r).toFixed(2) + " BDT"
          );

          return r;
        }),

        unis(c.cca2).then(function (u) {
          if (u.unavailable) {
            step(
              2,
              "er",
              "university source unavailable; adding country profile anyway"
            );
          } else {
            step(
              2,
              "ok",
              u.length + " institutions with an official website"
            );
          }

          return u;
        })
      ]);
    })
      .then(function (v) {
        var rate = v[0];
        var list = v[1];
        var P = RK.providers;
        var ranks = RK.ranks || {};
        var hits = {};

        Object.keys(P).forEach(function (p) {
          var table = ranks[p] || {};

          hits[p] = list.filter(function (u) {
            var r = table[norm(u.name)];
            return r && r.n != null;
          }).length;
        });

        step(
          3,
          "ok",
          Object.keys(P).map(function (p) {
            return P[p].short + " " + hits[p];
          }).join(", ") + " matched"
        );

        var rows = [
          ["Capital", (c.capital || ["n/a"]).join(", ")],
          ["Region", c.subregion || c.region || ""],
          [
            "Languages",
            Object.keys(c.languages || {}).map(function (k) {
              return c.languages[k];
            }).join(", ")
          ],
          [
            "Population",
            (c.population || 0).toLocaleString("en-US")
          ],
          ["Currency", cur],
          [
            "Exchange rate",
            "1 " + cur + " = " + (+rate).toFixed(2) +
            " BDT (" + day + ")"
          ]
        ];

        var ov =
          '<div class="card">' +
            '<div class="bd" style="border:0;padding:0"><dl>' +
              rows.map(function (r) {
                return (
                  "<dt>" + esc(r[0]) + "</dt>" +
                  "<dd>" + esc(r[1]) + "</dd>"
                );
              }).join("") +
            "</dl></div>" +
          "</div>" +
          '<div class="note">' +
            "Auto-built entry. Profile and country information come from a public country dataset; " +
            "exchange rates come from the exchange-rate service; universities come from Wikidata; " +
            "ranks come from the bundled QS and THE data. " +
            "Entry requirements, fees, deadlines, visa rules and scholarships are not auto-filled. " +
            "Confirm them on each university site and with the national immigration authority." +
          "</div>";

        var meta = {
          code: cc,
          name: name,
          flag: c.flag,
          currency: cur,
          title: "Study in " + name + ": Applicant Guide",
          sub: SUB,
          portal: "Wikidata",
          portal_url:
            "https://www.wikidata.org/wiki/Special:Search?search=" +
            encodeURIComponent(name + " university"),
          top_label: "",
          uni_title: name + " universities",
          prog_btn: "University website",
          list_note:
            "Universities come from Wikidata (institutions with an official website).",
          rank_note: "",
          gen_note:
            "Entry requirements, tuition fees and scholarships differ by programme. Open the university website and confirm with the official source.",
          caution:
            "<b>Auto-built entry:</b> verify every figure with the official source before advising a student."
        };

        CUS[cc] = {
          entry: {
            code: cc,
            name: name,
            flag: c.flag,
            dir: null,
            currency: cur,
            custom: true
          },

          facts: {
            last_checked: day,
            maintenance: {},
            institutions: {
              listed: list.length
            },
            links: {},
            fx: Object.fromEntries([
              [cur + "_BDT", rate],
              ["date", day],
              ["source", "exchange-rate service"]
            ])
          },

          universities: {
            source: "https://www.wikidata.org/",
            universities: list
          },

          content: {
            meta: meta,
            tabs: [
              ["overview", "Overview"],
              ["unis", "Universities"]
            ],
            links: {},
            req: {},
            steps: [],
            sections: {
              overview: {
                title: "Overview",
                html: ov
              }
            }
          }
        };

        save();

        CC.push(CUS[cc].entry);
        refreshSel();
        added();

        PICK = null;
        $("#cpick").textContent = "";

        setTimeout(function () {
          dlg.close();
          $("#cc").value = cc;
          setCountry(cc, "unis");
        }, 900);
      })
      .catch(function (e) {
        step(1, "er", "a data source did not respond");

        $("#clog").innerHTML = netfail();

        $("#cgo").disabled = false;
      });
  };
})();
