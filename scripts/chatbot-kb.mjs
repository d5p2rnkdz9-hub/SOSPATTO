#!/usr/bin/env node
// Genera la base di conoscenza del chatbot dalla KB testuale kb/ (tools/kb/build_kb.py, vedi tools/kb/README.md).
//
//   node scripts/chatbot-kb.mjs [percorso-KB]
//
// Scrive in netlify/chat/kb/ (letto da netlify/chat/core.mjs):
//   prompt.json — schede (metadati, massima, commento) + indice degli articoli: va nel system prompt, in cache
//   norme.json  — { "1348 art.13": {titolo, url, testo}, "1348 cons.27": … } per lo strumento leggi_norma
//   testi.json  — brani ricercabili (righe di norma, pagine dei testi integrali) per lo strumento cerca
//
// L'output è deterministico (ordine fisso, niente date): se cambia un byte cambia la cache del prompt.
// Prima di rigenerare, aggiornare la KB: npm run kb.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const KB = process.argv[2] || process.env.KB_DIR || path.join(ROOT, "kb");   // generata da npm run kb
const OUT = path.join(ROOT, "netlify/chat/kb");

const SEZ_NORME = ["1-norme-ue", "2-norme-italiane"];
const SEZ_SCHEDE = [
  ["2-normativa-schede", "Normativa italiana (schede)"],
  ["3-giurisprudenza", "Giurisprudenza"],
  ["4-circolari-prassi", "Circolari e prassi"],
  ["5-dottrina", "Dottrina"],
];

// I duplicati di iCloud («nome 2.md») non sono file della KB.
const mdFiles = (dir) =>
  fs.readdirSync(path.join(KB, dir))
    .filter((f) => f.endsWith(".md") && !/ \d+\.md$/.test(f))
    .sort();

const norm = (s) => s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/'/g, " ");

const TAG_RE = /^\[([a-z0-9-]+) ((?:art|cons|all)\.[^\s\]]+)/;

// ---------------------------------------------------------------- norme
const norme = {};
const indiceNorme = [];
const brani = [];

for (const sez of SEZ_NORME) {
  for (const f of mdFiles(sez)) {
    // «Citato in SOS Patto da: …»: fuori le schede pre-Patto, che il sito non pubblica.
    const lines = fs.readFileSync(path.join(KB, sez, f), "utf8")
      .replace(/(?:; )?[^;:\n]*\[pre-Patto\] \[[^\]]+\]/g, "").replace(/^(Citato in SOS Patto da:) ; /gm, "$1 ")
      .split("\n");
    const titoloAtto = lines[0].replace(/^# /, "");
    const fonte = (lines.find((l) => l.startsWith("Fonte: ")) || "").match(/https?:\/\/\S+/)?.[0] || "";
    const base = fonte.replace(/^https:\/\/www\.sospatto\.it/, "");
    indiceNorme.push(`\n### ${titoloAtto}\nURL: ${base}`);

    let cur = null; // sezione "## ..." corrente
    const flush = () => {
      if (!cur) return;
      const tagLine = cur.righe.find((l) => TAG_RE.test(l));
      if (!tagLine) return;
      const [, prefix, art] = tagLine.match(TAG_RE);
      const key = `${prefix} ${art}`;
      const anchor = art.startsWith("art.") ? `#art_${art.slice(4)}` : "";
      norme[key] = { titolo: `${titoloAtto} — ${cur.titolo}`, url: base + anchor, testo: cur.righe.join("\n").trim() };
      indiceNorme.push(`[${key}] ${cur.titolo.replace(/^(Articolo|Art\.) \S+ — /, "")}`);
    };

    for (const l of lines) {
      if (l.startsWith("## ")) {
        flush();
        cur = { titolo: l.slice(3).trim(), righe: [] };
        continue;
      }
      const m = l.match(TAG_RE);
      if (m && m[2].startsWith("cons.") && !cur) {
        // considerando: prima del primo articolo, uno per riga
        norme[`${m[1]} ${m[2]}`] = { titolo: `${titoloAtto} — considerando ${m[2].slice(5)}`, url: base, testo: l };
      }
      if (cur && !l.startsWith("### ")) cur.righe.push(l);
      if (m) {
        const k = `${m[1]} ${m[2].split(" ")[0]}`;
        const artKey = m[2].startsWith("cons.") ? `${m[1]} ${m[2]}` : `${m[1]} ${m[2].match(/^art\.[^\s]+?(?=\s|$)/)?.[0] || m[2]}`;
        brani.push({ tipo: "norma", rif: k, art: artKey, url: base, testo: l, n: norm(l) });
      }
    }
    flush();
  }
}

// ---------------------------------------------------------------- schede
const schede = [];
for (const [sez, etichetta] of SEZ_SCHEDE) {
  schede.push(`\n## ${etichetta}`);
  for (const f of mdFiles(sez)) {
    const txt = fs.readFileSync(path.join(KB, sez, f), "utf8");
    // Le schede pre-Patto sono nella KB ma non sul sito: il chatbot (pubblico) non le vede.
    if (/^- Regime: pre-Patto/m.test(txt)) continue;
    const titolo = txt.split("\n")[0].replace(/^# /, "");
    const url = (txt.match(/^- Scheda SOS Patto: (\S+)/m)?.[1] || "").replace(/^https:\/\/www\.sospatto\.it/, "");
    const [redazionale, ...integrali] = txt.split(/^## Testo integrale/m);
    const corpo = redazionale.replace(/^# .*\n/, "").replace(/^## /gm, "#### ").trim();
    schede.push(`\n### ${titolo}\n${corpo}`);

    // Testo integrale diviso per pagina: [p. N]
    for (const blocco of integrali) {
      const pdf = blocco.match(/^PDF: (\S+)/m)?.[1]?.replace(/^https:\/\/www\.sospatto\.it/, "") || url;
      const pagine = blocco.split(/^\[p\. (\d+)\]( \(OCR\))?$/m);
      for (let i = 1; i < pagine.length; i += 3) {
        const testo = pagine[i + 2].trim();
        if (!testo) continue;
        brani.push({
          tipo: etichetta.toLowerCase(), rif: titolo, pagina: Number(pagine[i]), ocr: !!pagine[i + 1],
          url, pdf, testo, n: norm(testo),
        });
      }
    }
  }
}

const prompt =
  "# SCHEDE PUBBLICATE SU SOS PATTO\n" +
  "(massime e commenti sono redazionali; il testo dei provvedimenti si legge con lo strumento cerca)\n" +
  schede.join("\n") +
  "\n\n# INDICE DEGLI ARTICOLI\n" +
  "(tag da passare a leggi_norma; l'URL dell'articolo è l'URL dell'atto + #art_N)\n" +
  indiceNorme.join("\n") + "\n";

fs.mkdirSync(OUT, { recursive: true });
fs.writeFileSync(path.join(OUT, "prompt.json"), JSON.stringify(prompt));
fs.writeFileSync(path.join(OUT, "norme.json"), JSON.stringify(norme));
fs.writeFileSync(path.join(OUT, "testi.json"), JSON.stringify(brani));

const mb = (s) => (Buffer.byteLength(s) / 1e6).toFixed(2) + " MB";
console.log(`KB: ${KB}`);
console.log(`prompt.json ${mb(prompt)} (~${Math.round(prompt.length / 3.5 / 1000)}k token stimati)`);
console.log(`norme.json  ${Object.keys(norme).length} voci`);
console.log(`testi.json  ${brani.length} brani, ${mb(JSON.stringify(brani))}`);
