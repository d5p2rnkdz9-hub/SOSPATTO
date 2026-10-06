#!/usr/bin/env node
// Stato delle traduzioni EN/FR delle schede (regole in TRADUZIONI.md).
//
//   npm run traduzioni                      → elenca traduzioni mancanti, ferme a un
//                                             italiano più vecchio, con campi tecnici
//                                             divergenti dall'originale, orfane
//   npm run traduzioni -- --stamp FILE...   → scrive in FILE (tradotto) l'impronta
//                                             `it_hash` dell'originale italiano
//
// Esce con codice 1 se c'è qualcosa da sistemare.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const matter = require('gray-matter');

const ROOT = path.join(__dirname, '..');
const LINGUE = ['en', 'fr'];
const SEZIONI = ['giurisprudenza', 'circolari', 'dottrina', 'normativa'];
// campi che devono restare identici all'italiano
const TECNICI = ['corte', 'numero', 'date', 'temi', 'pdf', 'norme_impliciti', 'esempio', 'titolo', 'autori'];
const LISTE_HREF = ['norme', 'allegati', 'links'];

const hashIt = (file) => crypto.createHash('sha1').update(fs.readFileSync(file)).digest('hex').slice(0, 12);
const mdIn = (dir) => (fs.existsSync(dir) ? fs.readdirSync(dir).filter((f) => f.endsWith('.md')) : []);
const norm = (v) => JSON.stringify(v instanceof Date ? v.toISOString().slice(0, 10) : v);

function originaleDi(tradotto) {
  const rel = path.relative(path.join(ROOT, 'content'), path.resolve(tradotto)).split(path.sep);
  if (!LINGUE.includes(rel[0]) || !SEZIONI.includes(rel[1])) return null;
  return path.join(ROOT, 'content', rel[1], rel.slice(2).join(path.sep));
}

function stamp(files) {
  for (const f of files) {
    const it = originaleDi(f);
    if (!it || !fs.existsSync(it)) { console.error(`✖ ${f}: nessun originale italiano`); process.exitCode = 1; continue; }
    const h = hashIt(it);
    let src = fs.readFileSync(f, 'utf8');
    if (!src.startsWith('---\n')) { console.error(`✖ ${f}: frontmatter assente`); process.exitCode = 1; continue; }
    if (/^it_hash:.*$/m.test(src.split('\n---')[0])) src = src.replace(/^it_hash:.*$/m, `it_hash: ${h}`);
    else src = src.replace(/^---\n/, `---\nit_hash: ${h}\n`);
    fs.writeFileSync(f, src);
    console.log(`✓ ${path.relative(ROOT, f)} ← ${h}`);
  }
}

function controlla() {
  const problemi = [];
  let ok = 0;
  for (const sez of SEZIONI) {
    const dirIt = path.join(ROOT, 'content', sez);
    for (const lang of LINGUE) {
      const dirTr = path.join(ROOT, 'content', lang, sez);
      const tradotti = new Set(mdIn(dirTr));
      for (const f of mdIn(dirIt)) {
        const it = path.join(dirIt, f);
        const tr = path.join(dirTr, f);
        const rel = `${lang}/${sez}/${f}`;
        if (!tradotti.has(f)) { problemi.push(`MANCA        ${rel}`); continue; }
        tradotti.delete(f);
        const a = matter(fs.readFileSync(it, 'utf8')).data;
        const b = matter(fs.readFileSync(tr, 'utf8')).data;
        let bene = true;
        if (b.it_hash !== hashIt(it)) { problemi.push(`DA AGGIORNARE ${rel} (l'italiano è cambiato dopo la traduzione)`); bene = false; }
        for (const k of TECNICI) {
          if (norm(a[k]) !== norm(b[k])) { problemi.push(`CAMPO ≠       ${rel}: ${k}`); bene = false; }
        }
        for (const k of LISTE_HREF) {
          const ha = (a[k] || []).map((x) => x.href), hb = (b[k] || []).map((x) => x.href);
          if (norm(ha) !== norm(hb)) { problemi.push(`HREF ≠        ${rel}: ${k}`); bene = false; }
        }
        if (bene) ok++;
      }
      for (const f of tradotti) problemi.push(`ORFANA       ${lang}/${sez}/${f} (nessun originale italiano)`);
    }
  }
  for (const p of problemi) console.log(p);
  console.log(`[traduzioni] ${ok} a posto, ${problemi.length} da sistemare`);
  if (problemi.length) process.exitCode = 1;
}

const args = process.argv.slice(2);
if (args[0] === '--stamp') stamp(args.slice(1));
else controlla();
