#!/usr/bin/env node
// Nelle schede delle circolari non si indica chi ha firmato l'atto (prefetti, viceprefetti,
// dirigenti, funzionari): si cita l'ufficio, mai la persona. Questo controllo ferma il build
// se in content/{,en/,fr/}circolari/ compare una formula di firma («a firma del», «firmata dal»,
// «signed by», «signée par», «f.to»…).
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..', 'content');
const dirs = ['circolari', 'en/circolari', 'fr/circolari'].map((d) => path.join(root, d));
const FIRMA = /\ba\s+firma\s+d|\bfirmat[aoie]\s+(da|dal|dalla|dallo|dai|dalle)\b|\bsottoscritt[aoie]\s+da|\bf\.\s?to\b|\bsigned\s+by\b|\bsign[ée]e?s?\s+(par|du|de\s+la)\b/i;

const errori = [];
for (const dir of dirs) {
  if (!fs.existsSync(dir)) continue;
  for (const f of fs.readdirSync(dir)) {
    if (!f.endsWith('.md') && !f.endsWith('.md.bozza')) continue;
    const rel = path.relative(path.join(__dirname, '..'), path.join(dir, f));
    // le righe a capo spezzano le formule: si controlla il testo con gli a capo normalizzati
    const testo = fs.readFileSync(path.join(dir, f), 'utf8').replace(/\s+/g, ' ');
    const m = testo.match(FIRMA);
    if (m) errori.push(`${rel}  («…${testo.slice(Math.max(0, m.index - 30), m.index + 60)}…»)`);
  }
}

if (errori.length) {
  console.error('[firmatari] nelle circolari non si indica chi ha firmato: citare solo l\'ufficio:');
  for (const e of errori) console.error('  ✗ ' + e);
  process.exit(1);
}
console.log('[firmatari] nessun firmatario nominato nelle circolari');
