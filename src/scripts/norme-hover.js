/* Tooltip sui riferimenti normativi delle schede (a.xref[data-act], generati in
 * build da scripts/norme-linker.js). Stessa resa del testo interattivo: al passaggio
 * del mouse si carica il data.js dell'atto dal bundle (una volta sola, solo se
 * serve) e si mostra l'articolo con il paragrafo/comma citato evidenziato.
 * Su touch non c'è hover: il link porta all'articolo nel testo interattivo. */
(function () {
  'use strict';
  if (!document.querySelector('a.xref[data-act]')) return;
  if (!window.matchMedia('(hover: hover)').matches) return;

  var BUNDLE = '/patto-interattivo/';
  var STORE = {};
  var loading = {};

  /* da dove si carica ogni atto, e rispetto a cosa si risolvono i link interni */
  function sorgente(key) {
    var m;
    if (/^\d+$/.test(key)) return { src: BUNDLE + 'assets/data.js', base: BUNDLE };
    if ((m = /^(dlgs|dl)-(\d{4})-(\d+)$/.exec(key))) {
      var dir = BUNDLE + m[1] + '-' + m[3] + '-' + m[2] + '/';
      return { src: dir + 'assets/data.js', base: dir };
    }
    return { src: BUNDLE + 'assets/data-ext/' + key + '.js', base: BUNDLE };
  }
  /* i data.js delle leggi italiane contengono anche stub «external» degli altri atti:
   * per Patto e leggi serve la versione completa, per gli atti esterni basta lo stub pieno */
  function pronto(key) {
    var a = STORE[key];
    if (!a) return false;
    if (/^\d+$/.test(key) || /^(dlgs|dl)-/.test(key)) return !a.external;
    return true;
  }
  function fondi() {
    var P = window.PACTO;
    if (!P || !P.acts) return;
    for (var k in P.acts) {
      var a = P.acts[k];
      if (!STORE[k] || !a.external || STORE[k].external) STORE[k] = a;
    }
    window.PACTO = { acts: STORE };
  }
  function assicura(key, cb) {
    if (pronto(key)) return cb(true);
    var s = sorgente(key);
    if (loading[s.src]) { loading[s.src].push(cb); return; }
    loading[s.src] = [cb];
    window.PACTO = window.PACTO || { acts: STORE }; /* i data-ext scrivono in window.PACTO.acts */
    var el = document.createElement('script');
    el.src = s.src;
    el.onload = el.onerror = function () {
      fondi();
      var ok = pronto(key);
      (loading[s.src] || []).forEach(function (f) { f(ok); });
      delete loading[s.src];
    };
    document.head.appendChild(el);
  }

  /* ---------------- contenuto ---------------- */
  function articleHTML(key, art, par, full) {
    var act = STORE[key];
    var a = act && act.articles && act.articles[art];
    if (!a) return null;
    var ver = act.external && act.version ? ' <span class="t-ver">' + act.version + '</span>' : '';
    var head = '<div class="tip-head"><span class="t-act">' + act.label + '</span>' + ver +
      '<div class="t-label">' + a.label + '</div>' +
      (a.heading ? '<div class="t-heading">' + a.heading + '</div>' : '') + '</div>';
    var body = '';
    var parNum = par ? parseInt(par, 10) : null;
    var shown = 0;
    for (var i = 0; i < a.frags.length; i++) {
      var f = a.frags[i];
      if (!full && parNum !== null) {
        if (f[0] === parNum) { body += '<span class="hl-par">' + f[1] + '</span>'; shown++; }
      } else {
        body += (parNum !== null && f[0] === parNum) ? '<span class="hl-par">' + f[1] + '</span>' : f[1];
        shown++;
      }
    }
    if (!shown) for (i = 0; i < a.frags.length; i++) body += a.frags[i][1];
    return head + '<div class="tip-body">' + body + '</div>';
  }
  function recitalHTML(key, n) {
    var act = STORE[key];
    var r = act && act.recitals && act.recitals[n];
    if (!r) return null;
    return '<div class="tip-head"><span class="t-act">' + act.label + '</span>' +
      '<div class="t-label">Considerando (' + n + ')</div></div><div class="tip-body">' + r + '</div>';
  }
  function actHTML(key) {
    var act = STORE[key];
    if (!act) return null;
    var note = act.external ? 'Atto esterno al Patto' + (act.version ? ' — ' + act.version : '') + '. Clic per aprire il testo.'
                            : 'Clic per aprire il testo completo.';
    return '<div class="tip-head"><span class="t-act">' + act.label + '</span>' +
      '<div class="t-label">' + (act.short || '') + '</div></div><div class="tip-body tip-nota">' + note + '</div>';
  }
  function contenuto(link, full) {
    var key = link.getAttribute('data-act');
    var art = link.getAttribute('data-art');
    var rct = link.getAttribute('data-rct');
    var par = link.getAttribute('data-par');
    if (rct) return recitalHTML(key, rct);
    if (art) return articleHTML(key, art, par, full);
    return actHTML(key);
  }

  /* i frammenti del bundle hanno link relativi alla pagina dell'atto: si riportano
   * al percorso assoluto, così funzionano anche da /giurisprudenza/… */
  function sistemaLink(key) {
    var s = sorgente(key);
    var act = STORE[key] || {};
    var file = act.file || '';
    tip.querySelectorAll('a[href]').forEach(function (a) {
      var h = a.getAttribute('href');
      if (/^(https?:|mailto:|\/)/.test(h)) return;
      if (h.charAt(0) === '#') { a.setAttribute('href', s.base + file.replace(/^\.\.\/[^/]+\//, '') + h); return; }
      try { a.setAttribute('href', new URL(h, location.origin + s.base).pathname + (new URL(h, location.origin + s.base).hash)); } catch (e) { /* lascia com'è */ }
    });
  }

  /* ---------------- tooltip ---------------- */
  var tip = document.createElement('div');
  tip.id = 'norme-tip';
  tip.className = 'norme-tip';
  tip.hidden = true;
  document.body.appendChild(tip);

  var tipTimer = null, hideTimer = null, tipLink = null;

  function posiziona(link) {
    var r = link.getBoundingClientRect();
    tip.style.left = '0px'; tip.style.top = '0px';
    var w = Math.min(560, window.innerWidth * 0.88);
    var x = Math.min(Math.max(8, r.left + window.scrollX), window.scrollX + window.innerWidth - w - 12);
    var sotto = r.bottom + 370 < window.innerHeight;
    tip.style.left = x + 'px';
    if (sotto) tip.style.top = (r.bottom + window.scrollY + 6) + 'px';
    else tip.style.top = Math.max(window.scrollY + 8, r.top + window.scrollY - tip.offsetHeight - 6) + 'px';
  }

  function mostra(link, full) {
    var key = link.getAttribute('data-act');
    if (!pronto(key)) {
      tipLink = link;
      tip.innerHTML = '<div class="tip-body tip-nota">Caricamento…</div>';
      tip.hidden = false;
      posiziona(link);
      assicura(key, function (ok) {
        if (tipLink !== link) return;
        if (ok) mostra(link, full); else tip.hidden = true;
      });
      return;
    }
    var html = contenuto(link, full);
    if (!html) { tip.hidden = true; return; }
    tipLink = link;
    var par = link.getAttribute('data-par');
    var foot = (par && !full) ? '<div class="tip-foot"><a id="norme-tip-full">Mostra l’articolo completo</a></div>' : '';
    tip.innerHTML = html + foot;
    sistemaLink(key);
    tip.hidden = false;
    posiziona(link);
    var fl = document.getElementById('norme-tip-full');
    if (fl) fl.addEventListener('click', function (e) { e.preventDefault(); mostra(link, true); });
    var hp = tip.querySelector('.hl-par');
    if (hp) tip.scrollTop = Math.max(0, hp.offsetTop - 60);
  }
  function nascondiPresto() {
    hideTimer = setTimeout(function () { tip.hidden = true; tipLink = null; }, 250);
  }

  document.addEventListener('mouseover', function (e) {
    var link = e.target.closest && e.target.closest('a.xref[data-act]');
    if (link && !tip.contains(link)) {
      clearTimeout(hideTimer); clearTimeout(tipTimer);
      tipTimer = setTimeout(function () { mostra(link, false); }, 180);
    } else if (tip.contains(e.target)) {
      clearTimeout(hideTimer);
    }
  });
  document.addEventListener('mouseout', function (e) {
    var link = e.target.closest && e.target.closest('a.xref[data-act]');
    if (link && !tip.contains(link)) { clearTimeout(tipTimer); nascondiPresto(); }
    else if (tip.contains(e.target)) nascondiPresto();
  });
  tip.addEventListener('mouseenter', function () { clearTimeout(hideTimer); });
  tip.addEventListener('mouseleave', nascondiPresto);
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') { tip.hidden = true; tipLink = null; } });
})();
