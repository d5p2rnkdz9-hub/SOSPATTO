// Trasforma le citazioni normative nel testo delle schede («art. 42, par. 1, lett. j)
// Reg. (UE) 2024/1348», «art. 35-bis, comma 3, d.lgs. 25/2008») in link `a.xref`
// verso il testo interattivo, con gli stessi attributi data-act/data-art/data-par
// del bundle: il tooltip lato client (src/scripts/norme-hover.js) li legge da lì.
//
// Ogni link viene emesso solo se l'anchor esiste davvero nel file del bundle
// (id="art_42", id="042.001", id="art_35-bis-com3", id="rct_17"): le citazioni che
// non risolvono restano testo e finiscono nel riepilogo di fine build.
//
// Le citazioni senza atto («l'art. 43, par. 1, richiama…») si risolvono sul
// contesto in modo prudente. Candidati sono gli atti citati nel testo — compresi
// quelli SENZA testo interattivo (d.l. 13/2017, d.m., c.p.c.…), che possono
// «vincere» e in tal caso la citazione resta testo — filtrati per tipo («par.» ⇒
// atto UE, «comma» o suffisso -bis/-ter ⇒ legge italiana) e per esistenza
// dell'articolo. Poi, nell'ordine: l'articolo è fra le «Norme collegate» della
// scheda; l'atto è citato nello stesso paragrafo; è il più vicino (prima quello
// che precede, poi quello che segue). Se resta più di un candidato, testo.
//
// Usato da eleventy.config.mjs (transform) e da `npm run norme-check`.
const fs = require('fs');
const path = require('path');

const BUNDLE_DIR = path.join(__dirname, '..', 'public', 'patto-interattivo');
const BUNDLE_URL = '/patto-interattivo/';

// Atti del Patto: numero -> file. Chiave data-act = numero (come nel bundle).
const PATTO = new Set(['1346', '1347', '1348', '1349', '1350', '1351', '1352', '1356', '1358', '1359']);
const NOMI = { procedure: '1348', accoglienza: '1346', screening: '1356', qualifiche: '1347', dublino: '1351', ramm: '1351', eurodac: '1358' };

// Leggi italiane presenti nel bundle: chiave data-act -> cartella.
const LEGGI = {
  'dlgs-2008-25': 'dlgs-25-2008',
  'dlgs-2015-142': 'dlgs-142-2015',
  'dlgs-1998-286': 'dlgs-286-1998',
  'dlgs-2007-251': 'dlgs-251-2007',
  'dl-2026-100': 'dl-100-2026',
};
const CARTELLA_A_KEY = Object.fromEntries(Object.entries(LEGGI).map(([k, v]) => [v, k]));

// Atti che non hanno un testo interattivo ma una scheda sul sito (chiave -> URL della
// scheda). Vuoto da quando il d.l. 100/2026 ha il suo testo interattivo (LEGGI).
const SCHEDE = {};

// ---- id presenti nei file del bundle (cache per file) -----------------------
const idCache = new Map();
function idsDi(relFile) {
  if (idCache.has(relFile)) return idCache.get(relFile);
  const full = path.join(BUNDLE_DIR, relFile);
  let set = null;
  if (fs.existsSync(full)) {
    set = new Set();
    const html = fs.readFileSync(full, 'utf8');
    const re = /\sid="([^"]+)"/g;
    let m;
    while ((m = re.exec(html))) set.add(m[1]);
  }
  idCache.set(relFile, set);
  return set;
}

function attoDaKey(key) {
  if (PATTO.has(key)) return { key, file: `${key}.html`, base: BUNDLE_URL };
  if (LEGGI[key]) return { key, file: `${LEGGI[key]}/index.html`, base: `${BUNDLE_URL}${LEGGI[key]}/` };
  const file = `ext-${key}.html`;
  if (idsDi(file)) return { key, file, base: BUNDLE_URL, ext: true };
  return null;
}
// 'dir' | 'reg' | 'it' — anche per le chiavi degli atti non linkabili («?dl-2017-13»)
function tipoAtto(key) {
  const k = key.replace(/^\?/, '');
  if (k === '1346' || k.startsWith('dir-')) return 'dir';
  if (/^(dlgs|dl|dm|l)(-|$)/.test(k)) return 'it';
  return 'reg';
}

// ---- risoluzione dell'atto ---------------------------------------------------
// Ritorna { key, file, base } | { scheda, nl } | { nl } (atto riconosciuto ma senza
// testo interattivo: chiave «?…» usata solo come contesto) | null.
function risolviAtto(txt) {
  const t = txt.replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();
  let m;
  // Regolamento procedure, Direttiva accoglienza, Regolamento screening…
  if ((m = /^(?:Reg(?:olamento)?\.?|Dir(?:ettiva)?\.?)\s+(procedure|accoglienza|screening|qualifiche|dublino|ramm|eurodac)\b/i.exec(t))) {
    return attoDaKey(NOMI[m[1].toLowerCase()]);
  }
  // Reg. (UE) 2024/1348, Reg. UE n. 1348/2024, Reg. 1348, reg. 2024/1348, direttiva 2013/32/UE, Dir. (UE) 2024/1346
  if ((m = /^(Reg|Dir)\w*\.?\s*(?:\(?(?:UE|CE)\)?\s*)?(?:n\.\s*)?(\d+)(?:\/(\d+))?/i.exec(t))) {
    const tipo = m[1].toLowerCase();
    let anno, num;
    if (!m[3]) { anno = '2024'; num = m[2]; }
    else if (/^(19|20)\d\d$/.test(m[2]) && !/^(19|20)\d\d$/.test(m[3])) { anno = m[2]; num = m[3]; }
    else if (/^(19|20)\d\d$/.test(m[3])) { anno = m[3]; num = m[2]; }
    else { anno = m[2]; num = m[3]; }
    if (anno === '2024' && PATTO.has(num)) return attoDaKey(num);
    if (!m[3]) return null; // «Reg. 604» senza anno: non si indovina
    const key = `${tipo}-${anno}-${num}`;
    return attoDaKey(key) || { nl: `?${key}` };
  }
  if ((m = /^(?:d\.\s?lgs\.?|decreto legislativo)\s*(?:n\.\s*)?(\d+)\/(\d{4})/i.exec(t))) {
    const key = `dlgs-${m[2]}-${m[1]}`;
    return attoDaKey(key) || { nl: `?${key}` };
  }
  if (/^(?:t\.u\.|TUI|testo unico)/i.test(t)) return attoDaKey('dlgs-1998-286');
  if ((m = /^(?:d\.\s?l\.|decreto-legge)\s*(?:n\.\s*)?(\d+)\/(\d{4})/i.exec(t))) {
    const key = `dl-${m[2]}-${m[1]}`;
    return attoDaKey(key) || (SCHEDE[key] ? { scheda: SCHEDE[key], nl: `?${key}` } : { nl: `?${key}` });
  }
  if (/^(?:d\.\s?m\.|decreto (?:ministeriale|del Ministro))/i.test(t)) return { nl: '?dm' };
  return null;
}

// (key, art) delle «Norme collegate»: da href tipo /patto-interattivo/1348.html#042.001
function preferitiDaHref(hrefs) {
  const set = new Set();
  for (const h of hrefs || []) {
    const m = /^\/patto-interattivo\/([^#?]+)(?:#(.+))?$/.exec(h);
    if (!m) continue;
    let key = null;
    const p = m[1];
    if (/^\d+\.html$/.test(p)) key = p.replace('.html', '');
    else if (/^ext-.+\.html$/.test(p)) key = p.replace(/^ext-/, '').replace('.html', '');
    else { const c = p.split('/')[0]; key = CARTELLA_A_KEY[c] || null; }
    if (!key) continue;
    set.add(key);
    const hash = m[2] || '';
    let art = null;
    let mm;
    if ((mm = /^art_(.+?)(?:-com.*)?$/.exec(hash))) art = mm[1];
    else if ((mm = /^(\d{3})\.\d{3}$/.exec(hash))) art = String(parseInt(mm[1], 10));
    if (art) set.add(`${key}#${art}`);
  }
  return set;
}

// ---- grammatica delle citazioni -----------------------------------------------
// I segmenti su cui si lavora possono contenere <em>/<i>/<strong>/<b> inline:
// i suffissi latini in corsivo («35-*bis*») arrivano come «35-<em>bis</em>».
const EM_O = '(?:<(?:em|i)>)?';
const EM_C = '(?:</(?:em|i)>)?';
const SUF = '(?:bis|ter|quater|quinquies|sexies|septies|octies|novies|decies)';
const NUM = `\\d+(?:[- ]${EM_O}${SUF}${EM_C})?(?:\\.\\d+)?`;
const NUM_C = `\\d+(?:[- ]${EM_O}${SUF}${EM_C})?`;
const PAR = `(?:,?\\s*(?:par|parr|paragraf[oi])\\.?\\s*\\d+(?:\\s*(?:,|e|ed|o)\\s*\\d+)*)`;
const COMMA = `(?:,?\\s*(?:comma|commi|co)\\.?\\s*${NUM_C}(?:\\s*(?:,|e|ed|o)\\s*${NUM_C})*)`;
const LETTERA = `${EM_O}[a-z](?:-${EM_O}${SUF}${EM_C})?${EM_C}(?:\\)|(?![a-z.]))`;
const LETT = `(?:,?\\s*(?:lett|letter[ae])\\.?\\s*${LETTERA}(?:\\s*(?:,|e|ed|o)\\s*${LETTERA})*)`;
const PUNTO = `(?:,?\\s*(?:punto|punti|n|nn)\\.?\\s*\\d+\\)?(?:\\s*(?:,|e|ed|o)\\s*\\d+\\)?)*)`;
const ROMANO = `(?:,?\\s*(?:i|ii|iii|iv|v|vi)\\)(?![a-z]))`;
const PERIODO = `(?:,?\\s*(?:primo|secondo|terzo|quarto|ultimo)\\s+periodo)`;
const QUAL = `(?:${PAR}|${COMMA}|${LETT}|${PUNTO}|${ROMANO}|${PERIODO})`;
const ITEM = `${NUM}(?:${QUAL}){0,4}`;
const LISTA = `${ITEM}(?:\\s*,\\s*${ITEM})*(?:\\s*,?\\s*(?:e|ed|o)\\s*${ITEM})?`;
const SEP = `(?:,)?\\s*(?:del|della|dello|di|dal|dalla)?\\s*`;
const ATTO = '(?:[Rr]eg(?:olamento)?\\.?|[Dd]ir(?:ettiva)?\\.?)\\s+(?:[Pp]rocedure|[Aa]ccoglienza|[Ss]creening|[Qq]ualifiche|[Dd]ublino|RAMM|[Ee]urodac)\\b'
  + '|(?:[Rr]eg(?:olamento)?\\.?|[Dd]ir(?:ettiva)?\\.?)\\s*(?:\\(?(?:UE|CE)\\)?\\s*)?(?:n\\.\\s*)?\\d+(?:\\/\\d+)?(?:\\/(?:UE|CE))?'
  + '|(?:d\\.\\s?lgs\\.?|D\\.\\s?Lgs\\.?|decreto legislativo)\\s*(?:n\\.\\s*)?\\d+\\/\\d{4}'
  + '|(?:d\\.\\s?l\\.|D\\.\\s?L\\.|decreto-legge)\\s*(?:n\\.\\s*)?\\d+\\/\\d{4}'
  + '|(?:d\\.\\s?m\\.|D\\.\\s?M\\.|decreto (?:ministeriale|del Ministro))(?:\\s+\\d{1,2}\\s+\\w+\\s+\\d{4}|\\s+\\d{4})?'
  + '|t\\.u\\.(?:\\s*imm\\w*)?|\\bTUI\\b';

// art. 42, par. 1, lett. j) Reg. (UE) 2024/1348   |   artt. 5-ter e 5-quater d.lgs. 142/2015
const RE_ART = new RegExp(`\\b(artt?|Artt?)\\.\\s*(${LISTA})(${SEP})(${ATTO})`, 'g');
// considerando 17 e 20 Reg. (UE) 2024/1348
const RE_RCT = new RegExp(`\\b(considerando|cons\\.)\\s+(\\d+)((?:\\s*(?:,|e|ed|o)\\s*\\d+)*)(${SEP})(${ATTO})`, 'g');
// atto citato da solo
const RE_ATTO = new RegExp(`(${ATTO})`, 'g');
// citazione senza atto, con eventuale rinvio generico («del regolamento», «dello stesso decreto»)
const HINT = `(?:\\s*(?:del|della|dello)\\s+(?:(stesso|medesimo|citato|predetto)\\s+)?(regolamento|direttiva|decreto legislativo|decreto)(?:\\s+(?:[Pp]rocedure|[Aa]ccoglienza|[Ss]creening))?(?![\\w/]))?`;
const RE_ORFANO = new RegExp(`\\b(artt?|Artt?)\\.\\s*(${LISTA})${HINT}`, 'g');
// dopo una citazione orfana: se segue un altro atto (che non sappiamo linkare), non si indovina
const RE_ALTRO_ATTO = /^,?\s*(?:del|della|dello|di|dal|dalla)?\s*(?:Cost\b|c\.p\.c\.|c\.p\.|c\.c\.|CEDU|Carta|TFUE|TUE|d\.m\.|D\.M\.|d\.p\.r\.|D\.P\.R\.|l\.\s*n?\.?\s*\d|legge|[Dd]ir\.|[Dd]irettiva|[Rr]eg\.|[Rr]egolamento\s+\(?(?:UE|CE|\d)|d\.\s?lgs|D\.\s?Lgs|d\.\s?l\.|D\.\s?L\.|decreto[- ]legge|decreto ministeriale|decreto del Ministro|codice|Convenzione|Protocollo|Statuto|Trattato)/;
const RE_ITEM = new RegExp(`(${NUM})((?:${QUAL}){0,4})`, 'g');
const RE_PAR_N = /(?:par|parr|paragraf[oi])\.?\s*(\d+)/i;
const RE_COMMA_N = new RegExp(`(?:comma|commi|co)\\.?\\s*(${NUM_C})`, 'i');
const RE_CODA = /\s*(?:,|e|ed|o)\s*$/; // connettivo rimasto in coda alla citazione: fuori dal link

function pulisci(s) { return s.replace(/<[^>]+>/g, ''); }
function artKey(s) { return pulisci(s).replace(/\s+/g, '-'); }
function pad3(n) { return String(n).padStart(3, '0'); }
function primoArt(item) { return artKey(item.match(new RegExp(NUM))[0]); }
function marcaNL(key, testo) { return `<!--nl:${key.replace(/^\?/, '')}-->${testo}`; }

// Anchor per un articolo (+ paragrafo/comma se esiste). null se l'articolo non c'è.
function anchorArticolo(atto, art, quals) {
  const ids = idsDi(atto.file);
  if (!ids || !ids.has(`art_${art}`)) return null;
  let anchor = `art_${art}`;
  let par = null;
  const qtxt = pulisci(quals || '');
  let m;
  if (tipoAtto(atto.key) !== 'it' && (m = RE_PAR_N.exec(qtxt))) {
    const pid = `${pad3(art)}.${pad3(m[1])}`;
    if (ids.has(pid)) { anchor = pid; par = m[1]; }
  } else if (tipoAtto(atto.key) === 'it' && (m = RE_COMMA_N.exec(qtxt))) {
    const c = pulisci(m[1]).replace(/\s+/g, '-');
    if (ids.has(`art_${art}-com${c}`)) { anchor = `art_${art}-com${c}`; par = String(parseInt(c, 10)); }
  }
  return { anchor, par };
}

function tagArticolo(atto, art, a, testo) {
  const coda = RE_CODA.exec(testo);
  const dentro = coda ? testo.slice(0, coda.index) : testo;
  const attrs = `class="xref" data-act="${atto.key}" data-art="${art}"${a.par ? ` data-par="${a.par}"` : ''}`;
  return `<a ${attrs} href="${atto.base}${path.basename(atto.file)}#${a.anchor}">${dentro}</a>${coda ? coda[0] : ''}`;
}

function linkAtto(atto, testo) {
  if (atto.scheda) return marcaNL(atto.nl, `<a class="xref xref-scheda" href="${atto.scheda}">${testo}</a>`);
  return `<a class="xref" data-act="${atto.key}" href="${atto.base}${path.basename(atto.file)}">${testo}</a>`;
}

// «artt. 5-ter, 5-quater e 5-quinquies»: un link per articolo. null se uno non esiste nell'atto.
function linkLista(atto, lista, ctx) {
  let out = '';
  let last = 0;
  let m;
  RE_ITEM.lastIndex = 0;
  while ((m = RE_ITEM.exec(lista))) {
    const art = artKey(m[1]);
    const a = anchorArticolo(atto, art, m[2]);
    if (!a) { ctx.warn(`art. ${art} non trovato in ${atto.key} (${atto.file})`); return null; }
    out += lista.slice(last, m.index) + tagArticolo(atto, art, a, m[0]);
    last = m.index + m[0].length;
    ctx.links++;
  }
  return out + lista.slice(last);
}

// 1) articoli + atto
function passaArticoli(seg, ctx) {
  return seg.replace(RE_ART, (tutto, artt, lista, sep, attoTxt) => {
    const atto = risolviAtto(attoTxt);
    if (!atto) { ctx.nonLinkabile(attoTxt); return tutto; }
    if (atto.scheda) { ctx.links++; return marcaNL(atto.nl, `<a class="xref xref-scheda" href="${atto.scheda}">${tutto}</a>`); }
    if (atto.nl) { ctx.nonLinkabile(attoTxt); return marcaNL(atto.nl, tutto); }
    const items = lista.match(RE_ITEM) || [];
    if (items.length === 1) {
      const art = primoArt(items[0]);
      const a = anchorArticolo(atto, art, items[0]);
      if (!a) { ctx.warn(`art. ${art} non trovato in ${atto.key} (${atto.file})`); return tutto; }
      ctx.links++;
      return tagArticolo(atto, art, a, tutto);
    }
    const l = linkLista(atto, lista, ctx);
    if (l === null) return tutto;
    ctx.links++;
    const idx = tutto.indexOf(lista, artt.length + 1);
    return tutto.slice(0, idx) + l + sep + linkAtto(atto, attoTxt);
  });
}

// 2) considerando + atto
function passaConsiderando(seg, ctx) {
  return seg.replace(RE_RCT, (tutto, k, n, altri, sep, attoTxt) => {
    const atto = risolviAtto(attoTxt);
    if (!atto || atto.scheda || atto.nl || atto.ext) return tutto; // gli atti esterni non hanno i considerando
    const ids = idsDi(atto.file);
    if (!ids || !ids.has(`rct_${n}`)) { ctx.warn(`considerando ${n} non trovato in ${atto.key}`); return tutto; }
    ctx.links++;
    return `<a class="xref" data-act="${atto.key}" data-rct="${n}" href="${atto.base}${path.basename(atto.file)}#rct_${n}">${tutto}</a>`;
  });
}

// 3) atto citato da solo
function passaAtti(seg, ctx) {
  return seg.replace(RE_ATTO, (tutto) => {
    const atto = risolviAtto(tutto);
    if (!atto) { ctx.nonLinkabile(tutto); return tutto; }
    if (atto.nl && !atto.scheda) { ctx.nonLinkabile(tutto); return marcaNL(atto.nl, tutto); }
    ctx.links++;
    return linkAtto(atto, tutto);
  });
}

// 4) citazioni senza atto, risolte sul contesto
//   stato:      atti citati prima nel documento (per tipo), compresi i non linkabili «?…»
//   paragrafo:  atti citati nello stesso blocco (prima o dopo)
//   vicini:     [{ key, pos }] link/menzioni del blocco, per la distanza
//   preferiti:  Set di «key» e «key#art» dalle Norme collegate
function trasformaOrfani(seg, stato, paragrafo, vicini, basePos, preferiti, ctx) {
  return seg.replace(RE_ORFANO, (tutto, artt, lista, mod, hint, offset, intero) => {
    const dopo = intero.slice(offset + tutto.length);
    if (RE_ALTRO_ATTO.test(dopo)) return tutto; // «art. 13 Cost.», «art. 700 c.p.c.»: altro atto
    const contesto = () => pulisci(intero.slice(Math.max(0, offset - 50), offset + tutto.length + 50)).replace(/\s+/g, ' ');
    const items = lista.match(RE_ITEM) || [];
    const art0 = primoArt(items[0]);

    let candidati;
    if (hint === 'regolamento') candidati = stato.reg;
    else if (hint === 'direttiva') candidati = stato.dir;
    else if (hint === 'decreto legislativo' || (hint === 'decreto' && mod)) candidati = stato.it;
    else if (hint === 'decreto') return tutto; // «del decreto» nudo: potrebbe essere il provvedimento
    else {
      const q = pulisci(lista);
      const ue = RE_PAR_N.test(q);
      const it = RE_COMMA_N.test(q) || items.some((i) => new RegExp(`^\\d+(?:[- ]${SUF}|\\.\\d+)`).test(pulisci(i)));
      if (ue && !it) candidati = stato.ue;
      else if (it && !ue) candidati = stato.it;
      else candidati = stato.tutti;
    }
    candidati = [...new Set(candidati)];
    if (!candidati.length) { ctx.orfani.push(`${pulisci(tutto)}  ←  nessun atto citato prima  …${contesto()}…`); return tutto; }

    // esistenza dell'articolo (gli atti non linkabili «?…» non si possono escludere)
    const conArticolo = (k) => {
      if (k.startsWith('?')) return true;
      const atto = attoDaKey(k);
      return atto && items.every((i) => anchorArticolo(atto, primoArt(i), i));
    };
    let validi = candidati.filter(conArticolo);
    if (!validi.length) { ctx.orfani.push(`${pulisci(tutto)}  ←  articolo assente in ${candidati.join(', ')}  …${contesto()}…`); return tutto; }
    // fra le «Norme collegate» della scheda c'è proprio quest'articolo
    if (validi.length > 1) { const p = validi.filter((k) => preferiti.has(`${k}#${art0}`)); if (p.length) validi = p; }
    // citato nello stesso paragrafo
    if (validi.length > 1) { const p = validi.filter((k) => paragrafo.includes(k)); if (p.length) validi = p; }
    // il più vicino: prima chi precede, poi chi segue
    if (validi.length > 1) {
      const qui = basePos + offset;
      const scegli = (lista) => {
        let best = null, bestD = Infinity;
        for (const l of lista) {
          if (!validi.includes(l.key)) continue;
          const d = Math.abs(l.pos - qui);
          if (d < bestD) { bestD = d; best = l.key; }
        }
        return best;
      };
      const best = scegli(vicini.filter((l) => l.pos < qui)) || scegli(vicini.filter((l) => l.pos >= qui));
      if (best) validi = [best];
    }
    if (validi.length !== 1) {
      ctx.orfani.push(`${pulisci(tutto)}  ←  ambiguo tra ${validi.join(' e ')}  …${contesto()}…`);
      return tutto;
    }
    if (validi[0].startsWith('?')) {
      ctx.orfani.push(`${pulisci(tutto)}  ←  riferito a un atto senza testo interattivo (${validi[0].slice(1)})  …${contesto()}…`);
      return tutto;
    }
    const atto = attoDaKey(validi[0]);
    ctx.risolti.push(`${pulisci(tutto).replace(/\s+/g, ' ')} → ${atto.key}`);
    vicini.push({ key: atto.key, pos: basePos + offset }); // conta per le citazioni successive del paragrafo
    if (items.length === 1) {
      ctx.links++; ctx.impliciti++;
      return tagArticolo(atto, art0, anchorArticolo(atto, art0, items[0]), tutto);
    }
    const prima = ctx.links;
    const l = linkLista(atto, lista, ctx);
    ctx.impliciti += ctx.links - prima;
    const idx = tutto.indexOf(lista, artt.length + 1);
    return tutto.slice(0, idx) + l + tutto.slice(idx + lista.length);
  });
}

// Spezza l'HTML in segmenti: si salta tutto ciò che sta dentro <a>, <code>, <pre>,
// <script>, <style> e i tag stessi (compresi i marker <!--nl:…-->); i tag inline
// (em, i, strong, b) restano nel segmento così la regex può attraversarli.
const RE_TOKEN = /(<a\b[^>]*>[\s\S]*?<\/a>|<(?:code|pre|script|style)\b[^>]*>[\s\S]*?<\/(?:code|pre|script|style)>|<(?!\/?(?:em|i|strong|b)\b)[^>]+>)/i;
const RE_BLOCCO = /^<\/?(?:p|li|ul|ol|h[1-6]|blockquote|div|table|thead|tbody|tr|td|th|section|br|hr)\b/i;

function applica(html, fn) {
  const parti = html.split(new RegExp(RE_TOKEN.source, 'gi'));
  for (let i = 0; i < parti.length; i += 2) if (parti[i]) parti[i] = fn(parti[i]);
  return parti.join('');
}

// chiave dell'atto rappresentato da un token: link xref, oppure marker di atto non linkabile
function keyDelToken(tok) {
  let m = /^<a\b[^>]*\sdata-act="([^"]+)"/.exec(tok);
  if (m) return m[1];
  m = /^<!--nl:([^>]+)-->$/.exec(tok);
  if (m) return `?${m[1]}`;
  return null;
}

function linkNorme(html, opts = {}) {
  const preferiti = opts.preferiti instanceof Set ? opts.preferiti : preferitiDaHref(opts.hrefNorme || []);
  const ctx = {
    links: 0, impliciti: 0, risolti: [], warnings: [], orfani: [], nonLinkabili: new Map(),
    warn(msg) { this.warnings.push(msg); },
    nonLinkabile(t) { const k = pulisci(t).replace(/\s+/g, ' ').trim(); this.nonLinkabili.set(k, (this.nonLinkabili.get(k) || 0) + 1); },
  };
  // tre passate esplicite, ciascuna solo sul testo rimasto fuori dai link
  html = applica(html, (s) => passaArticoli(s, ctx));
  html = applica(html, (s) => passaConsiderando(s, ctx));
  html = applica(html, (s) => passaAtti(s, ctx));
  const fine = (h) => ({ html: h.replace(/<!--nl:[^>]+-->/g, ''), links: ctx.links, impliciti: ctx.impliciti,
    risolti: ctx.risolti, warnings: ctx.warnings, orfani: ctx.orfani, nonLinkabili: ctx.nonLinkabili });
  if (opts.impliciti === false) return fine(html);

  // quarta passata, in ordine di documento: le citazioni senza atto
  const tokens = html.split(new RegExp(RE_TOKEN.source, 'gi'));
  const bloccoDi = [];
  const posDi = [];
  const attiDelBlocco = [[]];
  const viciniDelBlocco = [[]];
  for (let i = 0, b = 0, pos = 0; i < tokens.length; i++) {
    if (i % 2 === 1) {
      if (RE_BLOCCO.test(tokens[i])) { b++; attiDelBlocco[b] = []; viciniDelBlocco[b] = []; }
      const k = keyDelToken(tokens[i]);
      if (k) {
        if (!attiDelBlocco[b].includes(k)) attiDelBlocco[b].push(k);
        viciniDelBlocco[b].push({ key: k, pos });
      }
    }
    bloccoDi[i] = b;
    posDi[i] = pos;
    pos += tokens[i].length;
  }
  const stato = { reg: [], dir: [], it: [], ue: [], tutti: [] };
  const ricorda = (st, k) => {
    const t = tipoAtto(k);
    if (!st[t].includes(k)) st[t].push(k);
    if (!st.tutti.includes(k)) st.tutti.push(k);
    if (t !== 'it' && !st.ue.includes(k)) st.ue.push(k);
  };
  for (let i = 0; i < tokens.length; i++) {
    if (i % 2 === 1) {
      const k = keyDelToken(tokens[i]);
      if (k) ricorda(stato, k);
    } else if (tokens[i]) {
      // nel paragrafo contano anche gli atti citati DOPO: si guardano insieme a quelli già visti
      const paragrafo = attiDelBlocco[bloccoDi[i]];
      const locale = { reg: [...stato.reg], dir: [...stato.dir], it: [...stato.it], ue: [...stato.ue], tutti: [...stato.tutti] };
      for (const k of paragrafo) ricorda(locale, k);
      tokens[i] = trasformaOrfani(tokens[i], locale, paragrafo, viciniDelBlocco[bloccoDi[i]], posDi[i], preferiti, ctx);
    }
  }
  return fine(tokens.join(''));
}

// Verifica che un href verso il bundle (es. dal frontmatter `norme:`) risolva.
function verificaHref(href) {
  if (!href || !href.startsWith(BUNDLE_URL)) return true;
  const [pathPart, hash] = href.slice(BUNDLE_URL.length).split('#');
  const ids = idsDi(pathPart || 'index.html');
  if (!ids) return false;
  return hash ? ids.has(hash) : true;
}

module.exports = { linkNorme, verificaHref, risolviAtto, preferitiDaHref, LEGGI, PATTO };
