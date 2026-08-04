#!/usr/bin/env node
// Verifica che ogni `temi:` nelle schede (content/**/*.md e .md.bozza) usi solo
// le label canoniche di _data/vocabolarioTemi.js. Uso: npm run temi-check
const fs = require('fs');
const path = require('path');

const vocab = require('../_data/vocabolarioTemi.js');
const labels = new Set(vocab.map((t) => t.label));
const aliasDi = {};
for (const t of vocab) for (const a of t.aliases) aliasDi[a.toLowerCase()] = t.label;

const root = path.join(__dirname, '..', 'content');
const files = [];
for (const dir of fs.readdirSync(root)) {
  const full = path.join(root, dir);
  if (!fs.statSync(full).isDirectory()) continue;
  for (const f of fs.readdirSync(full)) {
    if (f.endsWith('.md') || f.endsWith('.md.bozza')) files.push(path.join(full, f));
  }
}

let errori = 0;
for (const f of files) {
  const testo = fs.readFileSync(f, 'utf-8');
  const m = testo.match(/^temi:\s*\[(.*?)\]\s*$/m);
  const rel = path.relative(root, f);
  if (!m) {
    console.log(`⚠️  ${rel}: nessun campo temi`);
    continue;
  }
  const temi = m[1].split(',').map((t) => t.trim()).filter(Boolean);
  if (temi.length === 0) console.log(`⚠️  ${rel}: temi vuoto`);
  for (const t of temi) {
    if (!labels.has(t)) {
      errori++;
      const hint = aliasDi[t.toLowerCase()]
        ? ` (assorbito da «${aliasDi[t.toLowerCase()]}»)`
        : '';
      console.log(`✗ ${rel}: tema non canonico «${t}»${hint}`);
    }
  }
}

if (errori) {
  console.log(`\n${errori} tema/i non canonici. Vocabolario: _data/vocabolarioTemi.js`);
  process.exit(1);
}
console.log(`✓ ${files.length} schede verificate, tutti i temi sono canonici.`);
