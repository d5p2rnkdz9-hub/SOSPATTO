/* Selettore Nuovo / Vecchio / Modifiche, articolo per articolo.
 *
 * Il generatore (tools/testi-interattivi/versioni.py) marca ogni articolo modificato con data-ultima
 * (l'ultimo atto che l'ha toccato) e una riga <p class="amd-storia"> «Modificato dal …»;
 * qui ci si aggancia un selettore. La vista di un articolo è il suo data-vista:
 *   nuovo      testo in vigore (il soppresso sparisce, l'inserito è testo normale)
 *   vecchio    versione immediatamente precedente l'ultima modifica
 *   modifiche  differenze tra le due (la vista storica del bundle)
 * Tutto il nascondere/mostrare è in src/styles/versioni-testo.css; qui: bottoni, barra
 * «tutti gli articoli» (memoria in localStorage, ?v= nell'URL), bersagli dei rinvii per
 * versione (data-alt), title con la fonte (solo in Modifiche), ancore verso testo che la
 * vista nasconde, nota sulle anteprime.
 */
(function () {
  "use strict";
  var VISTE = { nuovo: 1, vecchio: 1, modifiche: 1 };
  var KEY = "sospatto-vista";
  var root = document.documentElement;
  var bar = document.getElementById("vista-bar");
  var avviso = bar && bar.querySelector(".vista-avviso");
  var main = document.querySelector("main.doc") || document.body;
  var articoli = [].slice.call(main.querySelectorAll(".art[data-ultima]"));
  if (!articoli.length) return;
  var NOMI = { nuovo: "testo nuovo", vecchio: "testo vecchio", modifiche: "confronto" };

  function vistaGlobale() {
    var v = root.getAttribute("data-vista");
    return VISTE[v] ? v : "nuovo";
  }
  function numero(art) {
    var n = art.querySelector(".oj-ti-art");
    return n ? n.textContent.replace(/\s+/g, " ").trim() : "";
  }

  /* ---------- rinvii: in Vecchio il <a> prende il bersaglio del testo vecchio ---------- */
  function attrs(el) {
    var o = {};
    for (var i = 0; i < el.attributes.length; i++) o[el.attributes[i].name] = el.attributes[i].value;
    return o;
  }
  function metti(el, o) {
    Object.keys(attrs(el)).forEach(function (k) { el.removeAttribute(k); });
    Object.keys(o).forEach(function (k) { el.setAttribute(k, o[k]); });
  }
  function bersagli(art, vecchio) {
    art.querySelectorAll("a[data-alt]").forEach(function (a) {
      if (vecchio && !a._nuovo) {
        var t = document.createElement("template");
        t.innerHTML = a.getAttribute("data-alt") + "</a>";
        var alt = t.content.firstChild;
        if (!alt || !alt.attributes) return;
        a._nuovo = attrs(a);
        var o = attrs(alt);
        ["data-alt", "data-fn", "data-fo"].forEach(function (k) {   /* marcatori del generatore */
          if (a._nuovo[k] != null) o[k] = a._nuovo[k];
        });
        metti(a, o);
      } else if (!vecchio && a._nuovo) {
        metti(a, a._nuovo);
        a._nuovo = null;
      }
    });
    /* link di una sola versione: fuori dal tab nell'altra */
    art.querySelectorAll("a[data-v]").forEach(function (a) {
      var vivo = a.getAttribute("data-v") === (vecchio ? "old" : "new");
      if (vivo) a.removeAttribute("tabindex"); else a.setAttribute("tabindex", "-1");
    });
  }

  /* ---------- title con la fonte della novella: solo in Modifiche ---------- */
  function titoli(art, on) {
    art.querySelectorAll("ins.amd-ins[title], del.amd-del[title], ins.amd-ins[data-amd-title], del.amd-del[data-amd-title]")
      .forEach(function (el) {
        if (on) {
          if (el.hasAttribute("data-amd-title")) el.setAttribute("title", el.getAttribute("data-amd-title"));
        } else if (el.hasAttribute("title")) {
          el.setAttribute("data-amd-title", el.getAttribute("title"));
          el.removeAttribute("title");
        }
      });
  }

  function applica(art, v) {
    if (art.getAttribute("data-vista") === v && art._pronto) return;
    art._pronto = true;
    art.setAttribute("data-vista", v);
    (art._bottoni || []).forEach(function (b) {
      b.setAttribute("aria-pressed", b.getAttribute("data-vista") === v ? "true" : "false");
    });
    bersagli(art, v === "vecchio");
    titoli(art, v === "modifiche");
  }

  /* ---------- selettore dentro la riga «Modificato dal …» ---------- */
  function selettore(etichetta) {
    var g = document.createElement("span");
    g.className = "vista-seg";
    g.setAttribute("role", "group");
    g.setAttribute("aria-label", etichetta);
    [["nuovo", "Nuovo"], ["vecchio", "Vecchio"], ["modifiche", "Modifiche"]].forEach(function (x) {
      var b = document.createElement("button");
      b.type = "button";
      b.setAttribute("data-vista", x[0]);
      b.setAttribute("aria-pressed", "false");
      b.textContent = x[1];
      g.appendChild(b);
    });
    return g;
  }
  articoli.forEach(function (art) {
    var riga = art.querySelector(".amd-storia");
    if (!riga) return;
    var ultima = art.getAttribute("data-ultima");
    var g = selettore("Versione dell'" + numero(art).replace(/^Art\./, "art."));
    g.querySelector('[data-vista="vecchio"]').title = "Testo prima del " + ultima;
    g.querySelector('[data-vista="modifiche"]').title = "Modifiche del " + ultima;
    riga.appendChild(g);
    if (art.classList.contains("art-new")) {
      var n = document.createElement("span");
      n.className = "vista-art-nota";
      n.textContent = "Prima del " + ultima + " questo articolo non esisteva.";
      riga.appendChild(n);
    }
    art._bottoni = [].slice.call(g.querySelectorAll("button"));
    g.addEventListener("click", function (e) {
      var b = e.target.closest("button[data-vista]");
      if (!b) return;
      fermo(art, function () { applica(art, b.getAttribute("data-vista")); });
    });
  });

  /* cambio vista senza perdere il punto di lettura: `ref` resta dov'era sullo schermo */
  function fermo(ref, fn) {
    var prima = ref.getBoundingClientRect().top;
    fn();
    var dopo = ref.getBoundingClientRect().top;
    if (dopo !== prima) {
      var st = root.style.scrollBehavior;
      root.style.scrollBehavior = "auto";
      window.scrollBy(0, dopo - prima);
      root.style.scrollBehavior = st;
    }
  }

  /* ---------- barra «tutti gli articoli» ---------- */
  var barBottoni = bar ? [].slice.call(bar.querySelectorAll(".vista-seg button[data-vista]")) : [];
  function tutti(v, ricorda) {
    root.setAttribute("data-vista", v);
    barBottoni.forEach(function (b) {
      b.setAttribute("aria-pressed", b.getAttribute("data-vista") === v ? "true" : "false");
    });
    articoli.forEach(function (art) { applica(art, v); });
    marcaAnteprime();
    if (!ricorda) return;
    try { localStorage.setItem(KEY, v); } catch (e) {}
    try {
      var u = new URL(location.href);
      u.searchParams.set("v", v);
      history.replaceState(history.state, "", u.pathname + u.search + u.hash);
    } catch (e) {}
  }
  function inCima() {
    var tb = document.querySelector(".topbar");
    var y = (tb ? tb.getBoundingClientRect().bottom : 0) + 12;
    var x = main.getBoundingClientRect().left + 40;
    var el = document.elementFromPoint(Math.max(1, x), Math.max(1, y));
    return el && el.closest && main.contains(el) ? el.closest(".art, h2.capo") : null;
  }
  barBottoni.forEach(function (b) {
    b.addEventListener("click", function () {
      var v = b.getAttribute("data-vista"), ref = inCima();
      mostraAvviso("");
      if (ref) fermo(ref, function () { tutti(v, true); }); else tutti(v, true);
    });
  });

  /* ---------- ancore verso testo nascosto dalla vista del suo articolo ---------- */
  var avvisoTimer = null;
  function mostraAvviso(msg) {
    if (!avviso) return;
    clearTimeout(avvisoTimer);
    avviso.textContent = msg || "";
    avviso.hidden = !msg;
    if (msg) avvisoTimer = setTimeout(function () { avviso.hidden = true; }, 8000);
  }
  function visibile(el) { return !!(el && el.getClientRects().length); }
  function vaiA(el) {
    var st = root.style.scrollBehavior, tb = document.querySelector(".topbar");
    root.style.scrollBehavior = "auto";
    window.scrollTo(0, el.getBoundingClientRect().top + window.scrollY - (tb ? tb.offsetHeight : 0) - 8);
    root.style.scrollBehavior = st;
  }
  function sblocca(el) {
    if (!el || !main.contains(el) || visibile(el)) return false;
    var art = el.closest(".art[data-ultima]");
    if (!art) return false;
    var da = art.getAttribute("data-vista") || vistaGlobale();
    applica(art, "modifiche");
    var n = numero(art).replace(/^Art\./, "L'art.") || "Il punto richiesto";
    mostraAvviso(n + " era aperto sul " + NOMI[da] + ", che non contiene il punto richiesto: mostro le modifiche.");
    return true;
  }
  function bersaglio(hash) {
    var id = (hash || "").replace(/^#/, "");
    if (!id) return null;
    try { id = decodeURIComponent(id); } catch (e) {}
    return document.getElementById(id);
  }
  /* in cattura, prima di app.js: così il suo scrollIntoView trova il bersaglio visibile */
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a[href*='#']");
    if (!a || a.matches("a.xref[data-art], a.xref[data-rct]")) return; /* quelli aprono il pannello */
    var href = a.getAttribute("href") || "";
    var i = href.indexOf("#"), pagina = href.slice(0, i);
    if (pagina && pagina !== "index.html" && pagina !== location.pathname) return;
    sblocca(bersaglio(href.slice(i)));
  }, true);
  window.addEventListener("hashchange", function () {
    var el = bersaglio(location.hash);
    if (sblocca(el)) vaiA(el);
  });

  /* ---------- anteprime: i dati di app.js hanno il solo testo in vigore ---------- */
  var COORD = {};
  var CUR = document.body.getAttribute("data-act");
  if (window.PACTO && window.PACTO.acts && window.PACTO.acts[CUR]) COORD[window.PACTO.acts[CUR].label] = 1;
  ["dlgs-2008-25", "dlgs-2015-142", "dlgs-1998-286", "dl-2026-100"].forEach(function (k) {
    var a = window.PACTO && window.PACTO.acts && window.PACTO.acts[k];
    if (a) COORD[a.label] = 1;
  });
  function marcaAnteprime() {
    ["tip", "panel-body"].forEach(function (id) {
      var box = document.getElementById(id);
      var head = box && box.querySelector(".tip-head");
      var act = head && head.querySelector(".t-act");
      var nota = box && box.querySelector(".vista-tipnota");
      var serve = vistaGlobale() === "vecchio" && act && COORD[act.textContent.trim()];
      if (nota && !serve) nota.parentNode.removeChild(nota);
      if (!serve || nota) return;
      var n = document.createElement("div");
      n.className = "vista-tipnota";
      n.textContent = "Anteprima nel testo in vigore.";
      head.parentNode.insertBefore(n, head.nextSibling);
    });
  }
  if ("MutationObserver" in window) {
    var mo = new MutationObserver(marcaAnteprime);
    ["tip", "panel-body"].forEach(function (id) {
      var box = document.getElementById(id);
      if (box) mo.observe(box, { childList: true });
    });
  }

  tutti(vistaGlobale(), false);
  var arrivo = bersaglio(location.hash);
  if (sblocca(arrivo)) {
    vaiA(arrivo);
    window.addEventListener("load", function () { setTimeout(function () { vaiA(arrivo); }, 80); });
  }
})();
