#!/usr/bin/env node
// Gli atti normativi (decreti-legge, decreti legislativi, leggi, decreti ministeriali) non sono
// circolari: stanno in «Normativa italiana», come testo interattivo o, se non ce l'hanno, come
// scheda in content/normativa/ (REDAZIONE.md § 7). Questo controllo ferma il build
// se in content/{,en/,fr/}circolari/ compare una scheda con nome file o `tipo` da atto normativo.
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..', 'content');
const dirs = ['circolari', 'en/circolari', 'fr/circolari'].map((d) => path.join(root, d));
const NOME = /^(dl|dlgs|legge|l)-\d+-\d{4}\b|^dm-/i;
const TIPO = /^(decreto[- ]legge|decreto legislativo|legge\b|d\.\s?l\.|d\.\s?lgs\.|decree[- ]law|legislative decree|law\b|act\b|d[ée]cret[- ]loi|d[ée]cret l[ée]gislatif|loi\b|decreto ministeriale|d\.\s?m\.|ministerial decree|d[ée]cret minist[ée]riel)/i;

const errori = [];
for (const dir of dirs) {
  if (!fs.existsSync(dir)) continue;
  for (const f of fs.readdirSync(dir)) {
    if (!f.endsWith('.md') && !f.endsWith('.md.bozza')) continue;
    const rel = path.relative(path.join(__dirname, '..'), path.join(dir, f));
    const fm = (fs.readFileSync(path.join(dir, f), 'utf8').match(/^---\n([\s\S]*?)\n---/) || [])[1] || '';
    const tipo = ((fm.match(/^tipo:\s*"?(.*?)"?\s*$/m) || [])[1] || '').trim();
    if (NOME.test(f) || TIPO.test(tipo)) errori.push(`${rel}  (tipo: «${tipo}»)`);
  }
}

if (errori.length) {
  console.error('[collocazione] atti normativi fra le circolari — vanno in «Normativa italiana» (REDAZIONE.md § 7):');
  for (const e of errori) console.error('  ✗ ' + e);
  process.exit(1);
}
console.log('[collocazione] nessun atto normativo fra le circolari');
