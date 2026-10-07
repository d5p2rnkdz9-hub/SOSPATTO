/* Patto interattivo — tooltip, pannello laterale, navigazione */
(function () {
  "use strict";
  var D = window.PACTO;
  if (!D) return;

  var CURRENT = document.body.getAttribute("data-act");
  var tip = document.getElementById("tip");

  /* dati degli atti esterni: caricati alla prima richiesta */
  var loadingExt = {};
  function ensureActData(key, cb) {
    if (D.acts[key]) return cb(true);
    if (!/^(reg|dir|dec)/.test(key)) return cb(false);
    if (loadingExt[key]) { loadingExt[key].push(cb); return; }
    loadingExt[key] = [cb];
    var s = document.createElement("script");
    s.src = "assets/data-ext/" + key + ".js" + (window.PACTO_V ? "?v=" + window.PACTO_V : "");
    s.onload = s.onerror = function () {
      var ok = !!D.acts[key];
      (loadingExt[key] || []).forEach(function (f) { f(ok); });
      delete loadingExt[key];
    };
    document.head.appendChild(s);
  }
  var panel = document.getElementById("panel");
  var panelBody = document.getElementById("panel-body");
  var panelCrumb = document.getElementById("panel-crumb");
  var panelBack = document.getElementById("panel-back");
  var panelGo = document.getElementById("panel-go");
  var chip = document.getElementById("return-chip");
  var canHover = window.matchMedia("(hover: hover)").matches;

  /* ---------------- rendering contenuti ---------------- */

  function actLabel(key) {
    return D.acts[key] ? D.acts[key].label : key;
  }

  function articleHTML(key, art, par, full) {
    var a = D.acts[key] && D.acts[key].articles[art];
    if (!a) return null;
    var act = D.acts[key];
    var ver = act.external ? ' <span class="t-ver">' + act.version + "</span>" : "";
    var h = '<div class="tip-head"><span class="t-act">' + actLabel(key) + "</span>" + ver +
      '<div class="t-label">' + a.label + "</div>" +
      (a.heading ? '<div class="t-heading">' + a.heading + "</div>" : "") + "</div>";
    var body = "";
    var parNum = par ? parseInt(par, 10) : null;
    var shown = 0;
    for (var i = 0; i < a.frags.length; i++) {
      var f = a.frags[i];
      if (!full && parNum !== null) {
        if (f[0] === parNum) {
          body += '<span class="hl-par">' + f[1] + "</span>";
          shown++;
        }
      } else {
        if (parNum !== null && f[0] === parNum) {
          body += '<span class="hl-par">' + f[1] + "</span>";
        } else {
          body += f[1];
        }
        shown++;
      }
    }
    if (!shown) {
      for (i = 0; i < a.frags.length; i++) body += a.frags[i][1];
    }
    return { head: h, body: '<div class="tip-body">' + body + "</div>", data: a };
  }

  function recitalHTML(key, n) {
    var r = D.acts[key] && D.acts[key].recitals[n];
    if (!r) return null;
    var h = '<div class="tip-head"><span class="t-act">' + actLabel(key) + "</span>" +
      '<div class="t-label">Considerando (' + n + ")</div></div>";
    return { head: h, body: '<div class="tip-body">' + r + "</div>" };
  }

  function buildContent(link, full) {
    var key = link.getAttribute("data-act");
    if (!key || !D.acts[key]) return null;
    var art = link.getAttribute("data-art");
    var rct = link.getAttribute("data-rct");
    var par = link.getAttribute("data-par");
    if (rct) return recitalHTML(key, rct);
    if (art) return articleHTML(key, art, par, !!full);
    var a = D.acts[key];
    var note = a.external ? "Atto esterno al Patto — " + a.version + ". Clic per aprire."
                          : "Clic per aprire il testo completo.";
    return {
      head: '<div class="tip-head"><span class="t-act">' + a.label + "</span>" +
        '<div class="t-label">' + a.short + "</div></div>",
      body: '<div class="tip-body" style="font-family:var(--sans);font-size:12.5px;color:#6e6e73">' +
        note + "</div>"
    };
  }

  /* ---------------- tooltip ---------------- */

  var tipTimer = null, hideTimer = null, tipLink = null;

  function positionTip(link) {
    var r = link.getBoundingClientRect();
    tip.style.left = "0px"; tip.style.top = "0px";
    var w = Math.min(560, window.innerWidth * 0.88);
    var x = Math.min(Math.max(8, r.left + window.scrollX), window.scrollX + window.innerWidth - w - 12);
    var below = r.bottom + 370 < window.innerHeight;
    var y = below ? r.bottom + window.scrollY + 6 : null;
    tip.style.left = x + "px";
    if (y !== null) {
      tip.style.top = y + "px";
    } else {
      tip.style.top = Math.max(window.scrollY + 8, r.top + window.scrollY - tip.offsetHeight - 6) + "px";
    }
  }

  function showTip(link, full) {
    var key = link.getAttribute("data-act");
    if (key && !D.acts[key]) {
      tipLink = link;
      tip.innerHTML = '<div class="tip-body" style="font-family:var(--sans);' +
        'font-size:12.5px;color:#6e6e73">Caricamento…</div>';
      tip.hidden = false;
      positionTip(link);
      ensureActData(key, function (ok) {
        if (tipLink !== link) return;
        if (ok) showTip(link, full); else tip.hidden = true;
      });
      return;
    }
    var c = buildContent(link, full);
    if (!c) return;
    tipLink = link;
    var par = link.getAttribute("data-par");
    var foot = "";
    if (par && !full) {
      foot = '<div class="tip-foot"><a id="tip-full">Mostra l’articolo completo</a></div>';
    }
    tip.innerHTML = c.head + c.body + foot;
    tip.hidden = false;
    positionTip(link);
    var fl = document.getElementById("tip-full");
    if (fl) fl.addEventListener("click", function (e) {
      e.preventDefault();
      showTip(link, true);
    });
    var hp = tip.querySelector(".hl-par");
    if (hp) tip.scrollTop = Math.max(0, hp.offsetTop - 60);
  }

  function hideTipSoon() {
    hideTimer = setTimeout(function () { tip.hidden = true; tipLink = null; }, 250);
  }

  if (canHover) {
    document.addEventListener("mouseover", function (e) {
      var link = e.target.closest && e.target.closest("a.xref");
      if (link && !link.classList.contains("ext")) {
        clearTimeout(hideTimer); clearTimeout(tipTimer);
        if (panel.contains(link)) return; /* dentro il pannello niente tooltip */
        tipTimer = setTimeout(function () { showTip(link, false); }, 180);
      } else if (tip.contains(e.target)) {
        clearTimeout(hideTimer);
      }
    });
    document.addEventListener("mouseout", function (e) {
      var link = e.target.closest && e.target.closest("a.xref");
      if (link) { clearTimeout(tipTimer); hideTipSoon(); }
      else if (tip.contains(e.target)) hideTipSoon();
    });
    tip.addEventListener("mouseenter", function () { clearTimeout(hideTimer); });
    tip.addEventListener("mouseleave", hideTipSoon);
  }

  /* ---------------- pannello laterale ---------------- */

  var crumbStack = [];

  function crumbLabel(link) {
    var key = link.getAttribute("data-act");
    var art = link.getAttribute("data-art");
    var rct = link.getAttribute("data-rct");
    var par = link.getAttribute("data-par");
    var s = D.acts[key] ? D.acts[key].short : key;
    if (rct) return s + " · cons. " + rct;
    var t = s + " · art. " + art;
    if (par) t += ", par. " + par;
    return t;
  }

  function renderPanel() {
    var top = crumbStack[crumbStack.length - 1];
    var c = buildContent(top.link, true);
    if (!c) return;
    panelBody.innerHTML = c.head + c.body;
    var parts = crumbStack.map(function (s, i) {
      return i === crumbStack.length - 1 ? "<b>" + s.label + "</b>" : s.label;
    });
    panelCrumb.innerHTML = parts.join(" → ");
    panelBack.hidden = crumbStack.length < 2;
    var href = top.link.getAttribute("href");
    panelGo.setAttribute("href", href);
    var topAct = D.acts[top.link.getAttribute("data-act")];
    var ex = document.getElementById("panel-eurlex");
    if (ex) {
      if (topAct && topAct.external) {
        ex.setAttribute("href", topAct.eurlex);
        ex.hidden = false;
      } else {
        ex.hidden = true;
      }
    }
    panel.hidden = false;
    panelBody.scrollTop = 0;
    var hp = panelBody.querySelector(".hl-par");
    if (hp) panelBody.scrollTop = Math.max(0, hp.offsetTop - panelBody.clientHeight / 3);
  }

  function openPanel(link) {
    tip.hidden = true;
    var key = link.getAttribute("data-act");
    ensureActData(key, function (ok) {
      if (!ok) { window.location.href = link.getAttribute("href"); return; }
      crumbStack.push({ link: link, label: crumbLabel(link) });
      renderPanel();
    });
  }

  function closePanel() {
    panel.hidden = true;
    crumbStack = [];
  }

  panelBack.addEventListener("click", function () {
    crumbStack.pop();
    if (crumbStack.length) renderPanel(); else closePanel();
  });
  document.getElementById("panel-close").addEventListener("click", closePanel);
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") { closePanel(); tip.hidden = true; }
  });

  /* ---------------- navigazione e chip di ritorno ---------------- */
  /* pila dei punti di lettura: sessionStorage quando disponibile (sopravvive
     ai cambi di pagina), altrimenti memoria della pagina corrente */

  var BACK_KEY = "pacto-back", RESTORE_KEY = "pacto-restore";
  var memStack = [];

  function pageFile() {
    return location.pathname.split("/").pop() || "index.html";
  }
  function getStack() {
    try {
      var s = JSON.parse(sessionStorage.getItem(BACK_KEY) || "null");
      if (s) return s;
    } catch (e) {}
    return memStack;
  }
  function setStack(s) {
    memStack = s;
    try { sessionStorage.setItem(BACK_KEY, JSON.stringify(s.slice(-30))); } catch (e) {}
  }
  function currentLabel() {
    var a = D.acts[CURRENT];
    if (a) return a.short;
    return (document.title.split("—")[0] || "").trim() || "pagina precedente";
  }
  function pushBack() {
    var s = getStack();
    s.push({ url: pageFile(), y: window.scrollY, label: currentLabel() });
    setStack(s);
    updateChip();
  }
  function updateChip() {
    var s = getStack();
    if (!s.length) { chip.hidden = true; return; }
    var top = s[s.length - 1];
    chip.textContent = top.url === pageFile()
      ? "↩ Torna al punto precedente"
      : "↩ Torna a " + top.label;
    chip.hidden = false;
  }
  function showChip() { updateChip(); }

  chip.addEventListener("click", function () {
    var s = getStack();
    var entry = s.pop();
    setStack(s);
    if (!entry) { updateChip(); return; }
    if (entry.url === pageFile()) {
      window.scrollTo({ top: entry.y, behavior: "smooth" });
      updateChip();
    } else {
      try { sessionStorage.setItem(RESTORE_KEY, JSON.stringify(entry)); } catch (e) {}
      window.location.href = entry.url;
    }
  });

  /* al caricamento: ripristina la posizione se si sta tornando indietro */
  (function () {
    try {
      var r = JSON.parse(sessionStorage.getItem(RESTORE_KEY) || "null");
      if (r && r.url === pageFile()) {
        sessionStorage.removeItem(RESTORE_KEY);
        setTimeout(function () {
          document.documentElement.style.scrollBehavior = "auto";
          window.scrollTo(0, r.y);
          document.documentElement.style.scrollBehavior = "";
        }, 60);
      }
    } catch (e) {}
    updateChip();
  })();

  function flashTarget(id) {
    var el = document.getElementById(id);
    if (!el) return;
    el.classList.remove("flash");
    void el.offsetWidth;
    el.classList.add("flash");
  }

  function goSamePage(anchor) {
    pushBack();
    var el = document.getElementById(anchor);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
      flashTarget(anchor);
      history.replaceState(null, "", "#" + anchor);
    }
  }

  document.addEventListener("click", function (e) {
    var link = e.target.closest && e.target.closest("a.xref");
    if (!link) return;
    if (link.classList.contains("ext")) return; /* EUR-Lex: comportamento normale */
    var href = link.getAttribute("href") || "";
    var hasPanel = link.getAttribute("data-art") || link.getAttribute("data-rct");

    if (hasPanel) {
      e.preventDefault();
      openPanel(link);
      return;
    }
    /* link ad atto intero, capo, parte o allegato */
    var hashIdx = href.indexOf("#");
    var page = hashIdx >= 0 ? href.slice(0, hashIdx) : href;
    var anchor = hashIdx >= 0 ? href.slice(hashIdx + 1) : "";
    var samePage = !page || page === pageFile();
    if (samePage && anchor) {
      e.preventDefault();
      goSamePage(anchor);
    } else {
      /* altra pagina: ricorda il punto di lettura, poi navigazione normale */
      pushBack();
    }
  });

  /* "Vai all'articolo" dal pannello */
  panelGo.addEventListener("click", function (e) {
    var href = panelGo.getAttribute("href") || "";
    var hashIdx = href.indexOf("#");
    var page = hashIdx >= 0 ? href.slice(0, hashIdx) : href;
    var anchor = hashIdx >= 0 ? href.slice(hashIdx + 1) : "";
    if (!page || page === pageFile()) {
      e.preventDefault();
      closePanel();
      if (anchor) goSamePage(anchor);
    } else {
      pushBack();
      closePanel();
    }
  });

  /* arrivo con hash da un'altra pagina: evidenzia il bersaglio */
  window.addEventListener("load", function () {
    if (location.hash.length > 1) flashTarget(location.hash.slice(1));
  });
  window.addEventListener("hashchange", function () {
    if (location.hash.length > 1) flashTarget(location.hash.slice(1));
  });

  /* ---------------- TOC: scrollspy + toggle mobile ---------------- */

  var tocLinks = {};
  document.querySelectorAll(".toc a.toc-art").forEach(function (a) {
    tocLinks[a.getAttribute("data-art")] = a;
  });
  var active = null;
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          var a = tocLinks[en.target.id];
          if (a) {
            if (active) active.classList.remove("active");
            a.classList.add("active");
            active = a;
          }
        }
      });
    }, { rootMargin: "0px 0px -75% 0px" });
    document.querySelectorAll("main.doc div[id^='art_']").forEach(function (el) {
      io.observe(el);
    });
  }

  var tocToggle = document.getElementById("toc-toggle");
  var toc = document.getElementById("toc");
  if (tocToggle && toc) {
    tocToggle.addEventListener("click", function () { toc.classList.toggle("open"); });
  }
  if (toc) {
    toc.addEventListener("click", function (e) {
      var a = e.target.closest("a");
      if (!a) return;
      toc.classList.remove("open");
      var href = a.getAttribute("href") || "";
      if (href.charAt(0) === "#") {
        e.preventDefault();
        goSamePage(href.slice(1));
      }
    });
  }

  /* evidenzia l'atto corrente nella barra */
  document.querySelectorAll(".actnav a").forEach(function (a) {
    if (a.getAttribute("href") === CURRENT + ".html") a.classList.add("current");
  });
})();
