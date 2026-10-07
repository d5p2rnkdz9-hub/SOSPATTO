/* Selettore Nuovo / Vecchio / Modifiche, articolo per articolo, per i testi del bundle.
 *
 * Le pagine public/patto-interattivo/<legge>/index.html sono generate a monte
 * (tools/testi-interattivi/, `npm run testi`, v. README) e una ricopia le
 * sovrascrive: per questo il selettore NON sta nel bundle, ma viene aggiunto
 * dalla build del sito (eleventy.config.mjs) sulle copie in _site/, e dal server
 * di sviluppo al volo. Il bundle resta com'è e l'rsync non lo può cancellare.
 *
 * Il generatore (tools/testi-interattivi/versioni.py) marca ogni articolo modificato con
 * data-ultima="<ultimo atto modificativo>" e una riga <p class="amd-storia">
 * «Modificato dal …» sotto la rubrica: qui si tocca solo chi ha quei marcatori.
 * Si aggiungono il CSS e lo snippet che sceglie la vista prima del primo paint (nel
 * <head>), la barra «tutti gli articoli» dopo il banner e lo script in fondo; i bottoni
 * di ogni articolo li crea lo script dentro la riga amd-storia.
 *
 * Lato browser: src/scripts/versioni-testo.js + src/styles/versioni-testo.css.
 */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const ROOT = path.join(__dirname, '..');
const CSS = 'src/styles/versioni-testo.css';
const JS = 'src/scripts/versioni-testo.js';
const MARK = '<!-- versioni:begin -->';

function ver(rel) {
  return crypto.createHash('sha1').update(fs.readFileSync(path.join(ROOT, rel))).digest('hex').slice(0, 8);
}

// vista di partenza di tutti gli articoli, decisa prima del primo paint: ?v= vince sulla
// scelta ricordata, «nuovo» è il default. I vecchi valori (vigente/previgente/confronto)
// valgono ancora, così i link già condivisi non si rompono.
const HEAD_SCRIPT = '<script>(function(){var M={vigente:"nuovo",previgente:"vecchio",confronto:"modifiche"},' +
  'V=/^(nuovo|vecchio|modifiche)$/,v=null,d=document.documentElement;' +
  'try{v=new URLSearchParams(location.search).get("v")}catch(e){}v=M[v]||v;' +
  'if(!V.test(v||"")){try{v=localStorage.getItem("sospatto-vista")}catch(e){}v=M[v]||v}' +
  'd.setAttribute("data-vista",V.test(v||"")?v:"nuovo")})();</script>';

const BAR = `<div class="vista-bar" id="vista-bar">
  <span class="vista-bar-lbl" id="vista-bar-lbl">Tutti gli articoli modificati:</span>
  <div class="vista-seg" role="group" aria-labelledby="vista-bar-lbl">
    <button type="button" data-vista="nuovo" aria-pressed="false">Nuovo</button>
    <button type="button" data-vista="vecchio" aria-pressed="false">Vecchio</button>
    <button type="button" data-vista="modifiche" aria-pressed="false">Modifiche</button>
  </div>
  <p class="vista-desc">Sotto la rubrica di ogni articolo modificato trovi da quale atto e un selettore solo per quell'articolo.
    <b>Nuovo</b> è il testo in vigore; <b>Vecchio</b> la versione immediatamente precedente l'ultima modifica;
    <b>Modifiche</b> le differenze tra le due (<ins class="amd-ins">inserito</ins>, <del class="amd-del">soppresso</del>).
    <span class="vista-nota">Testo coordinato non ufficiale, a fini di studio: fa fede solo la Gazzetta Ufficiale.</span></p>
  <p class="vista-avviso" role="status" hidden></p>
</div>`;

/** html della pagina → html con il selettore (rifatto da capo se c'era già), oppure
 *  null se la pagina non ha articoli modificati. */
function injectVersioni(html) {
  if (!html.includes('class="amd-storia"')) return null;
  // ogni blocco è «begin … end\n» davanti a un punto fisso: toglierlo ridà l'originale
  html = html.replace(/<!-- versioni:begin -->[\s\S]*?<!-- versioni:end -->\n/g, '');
  const head = `${MARK}\n<link rel="stylesheet" href="/${CSS}?v=${ver(CSS)}">\n${HEAD_SCRIPT}\n<!-- versioni:end -->\n`;
  const bar = `${MARK}\n${BAR}\n<!-- versioni:end -->\n`;
  const tail = `${MARK}\n<script src="/${JS}?v=${ver(JS)}"></script>\n<!-- versioni:end -->\n`;

  let out = html.replace('</head>', () => head + '</head>');
  const banner = out.match(/<div class="amd-banner">[\s\S]*?<\/div>\n/);
  out = banner ? out.replace(banner[0], () => banner[0] + bar)
               : out.replace('<div class="layout">', () => bar + '<div class="layout">');
  out = out.replace(/<\/body>(?![\s\S]*<\/body>)/, () => tail + '</body>');
  return out;
}

/** Applica il selettore a tutte le <dir>/patto-interattivo/<legge>/index.html. */
function injectDir(siteDir) {
  const base = path.join(siteDir, 'patto-interattivo');
  if (!fs.existsSync(base)) return [];
  const fatti = [];
  for (const d of fs.readdirSync(base).sort()) {
    const f = path.join(base, d, 'index.html');
    if (!fs.existsSync(f)) continue;
    const out = injectVersioni(fs.readFileSync(f, 'utf8'));
    if (out) { fs.writeFileSync(f, out); fatti.push(d); }
  }
  return fatti;
}

/** Middleware del server di sviluppo: nel `--serve` Eleventy serve public/ senza
 *  copiarlo in _site/, quindi il selettore va aggiunto alla risposta. */
function devMiddleware(req, res, next) {
  const m = (req.url || '').match(/^\/patto-interattivo\/([\w-]+)\/(?:index\.html)?(?:[?#].*)?$/);
  if (!m) return next();
  const f = path.join(ROOT, 'public', 'patto-interattivo', m[1], 'index.html');
  if (!fs.existsSync(f)) return next();
  const out = injectVersioni(fs.readFileSync(f, 'utf8'));
  if (!out) return next();
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  res.end(out);
}

module.exports = { injectVersioni, injectDir, devMiddleware };
