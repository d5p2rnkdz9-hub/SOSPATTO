#!/usr/bin/env node
// Passa le schede (content/**/*.md e .md.bozza) nel linker delle norme e stampa,
// per file: link generati, citazioni che NON risolvono (articolo inesistente nel
// bundle), citazioni «orfane» (art. senza atto: restano testo) e href del
// frontmatter `norme:` che non risolvono. Uso: npm run norme-check [file...]
const fs = require('fs');
const path = require('path');
const markdownIt = require('markdown-it');
const { linkNorme, verificaHref } = require('./norme-linker.js');

const md = markdownIt({ html: true, linkify: true, typographer: true });
const root = path.join(__dirname, '..', 'content');

let files = process.argv.slice(2);
if (!files.length) {
  for (const dir of fs.readdirSync(root)) {
    const full = path.join(root, dir);
    if (!fs.statSync(full).isDirectory()) continue;
    for (const f of fs.readdirSync(full)) {
      if (f.endsWith('.md') || f.endsWith('.md.bozza')) files.push(path.join(full, f));
    }
  }
}

const verbose = process.env.NORME_VERBOSE === '1';
let totLinks = 0, totImpl = 0, totWarn = 0, totOrf = 0, totHref = 0;
const nonLinkabili = new Map();

for (const f of files.sort()) {
  const src = fs.readFileSync(f, 'utf8');
  // frontmatter (le bozze hanno righe di commento # prima del ---)
  const fm = /^(?:#[^\n]*\n)*---\n([\s\S]*?)\n---\n([\s\S]*)$/.exec(src);
  if (!fm) continue;
  const [, front, body] = fm;
  const massima = (/^(?:massima|oggetto|sommario): >-\n((?:[ \t]+[^\n]*\n?)+)|^(?:massima|oggetto|sommario): "(.*)"$/m.exec(front) || []);
  const testoMassima = (massima[1] || massima[2] || '').replace(/\n\s+/g, ' ');
  const html = `<div class="scheda-massima"><p>${testoMassima}</p></div>` + md.render(body);
  const hrefNorme = [...front.matchAll(/href:\s*"([^"]+)"/g)].map((m) => m[1]);
  const impliciti = !/^norme_impliciti:\s*false\b/m.test(front);
  const r = linkNorme(html, { hrefNorme, impliciti });
  for (const [k, v] of r.nonLinkabili) nonLinkabili.set(k, (nonLinkabili.get(k) || 0) + v);

  const hrefRotti = [];
  for (const m of front.matchAll(/href:\s*"([^"]+)"/g)) if (!verificaHref(m[1])) hrefRotti.push(m[1]);

  totLinks += r.links; totImpl += r.impliciti; totWarn += r.warnings.length; totOrf += r.orfani.length; totHref += hrefRotti.length;
  const rel = path.relative(path.join(__dirname, '..'), f);
  if (r.warnings.length || r.orfani.length || hrefRotti.length || verbose) {
    console.log(`\n${rel} — ${r.links} link (${r.impliciti} risolti dal contesto)`);
    for (const w of r.warnings) console.log(`  ✖ ${w}`);
    for (const h of hrefRotti) console.log(`  ✖ norme: href non risolve: ${h}`);
    for (const o of r.orfani) console.log(`  · resta testo: ${o}`);
    if (verbose) for (const s of r.risolti) console.log(`  ~ dal contesto: ${s}`);
  }
}

console.log(`\n[norme] ${files.length} schede — ${totLinks} link (${totImpl} risolti dal contesto), ${totWarn} citazioni non risolte, ${totHref} href rotti nel frontmatter, ${totOrf} citazioni rimaste testo`);
if (!verbose) console.log('[norme] NORME_VERBOSE=1 per vedere anche le citazioni risolte dal contesto (da rileggere per le schede nuove)');
if (nonLinkabili.size) {
  console.log('[norme] atti senza testo interattivo (restano testo): '
    + [...nonLinkabili.entries()].sort((a, b) => b[1] - a[1]).map(([k, v]) => `${k} ×${v}`).join('; '));
}
process.exit(totWarn || totHref ? 1 : 0);
