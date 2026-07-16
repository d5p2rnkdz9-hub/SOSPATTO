# SOS Patto

Sito statico (Eleventy) di **sospatto** — il Patto UE su migrazione e asilo, spiegato.
Clone in blu del tema di [sospermesso.it](https://www.sospermesso.it), deploy su Netlify.

## Sviluppo locale

```bash
npm install
npm run dev        # http://localhost:8080
npm run build      # genera _site/
```

## Struttura

```
_data/            dati: site.js (nome/URL/email), nav.js (menu), testi.js (catalogo dei 14 testi)
_includes/        layout base + header/nav/footer + layout schede (decisione, circolare)
src/pages/        pagine del sito (escono alla radice: /testi.html, /diagramma.html, ...)
src/styles/       tema clonato da sospermesso e ritinto in blu (+ appendice SOS Patto in components.css)
content/          giurisprudenza/ e circolari/ — UNA scheda = UN file .md
public/           copiato tale e quale alla radice del sito:
  patto-interattivo/   bundle dei testi interattivi (10 atti UE + 4 leggi italiane)
  diagramma/           Diagrammone (flowchart screening/procedure, file unico)
  allegati/            PDF di giurisprudenza e circolari
scripts/          retheme_blue.py — ritinta in blu i CSS (sito + bundle)
                  seo_bundle.py — inietta canonical/description/OG nel bundle
```

## Come aggiungere una DECISIONE (giurisprudenza)

1. Copia `content/giurisprudenza/esempio-tribunale-roma-2026.md` con un nome parlante,
   es. `trib-roma-2026-06-20-frontiera.md`.
2. Compila il frontmatter: `corte`, `tipo`, `numero`, `date` (AAAA-MM-GG), `temi`,
   `massima`, `norme` (etichetta + link all'articolo nel testo interattivo,
   es. `/patto-interattivo/1348.html` o `/patto-interattivo/dlgs-25-2008/index.html#art_32`).
   Togli `esempio: true`.
3. (Facoltativo) PDF del provvedimento **anonimizzato** in `public/allegati/giurisprudenza/`
   e percorso nel campo `pdf`.
4. Il corpo del file è il commento libero in Markdown.
5. `git add … && git commit && git push` → Netlify ricostruisce e pubblica da solo.

La scheda appare automaticamente in `/giurisprudenza.html` (ordinata per data
decrescente) e ha la sua pagina `/giurisprudenza/<nomefile>.html`.

## Come aggiungere una CIRCOLARE

Identico, in `content/circolari/` (campi: `ente`, `tipo`, `numero`, `date`, `temi`,
`oggetto`, `norme`, `pdf`). PDF in `public/allegati/circolari/`.

## Come aggiornare i TESTI INTERATTIVI

Il bundle vive in `public/patto-interattivo/` ed è **ritinto in blu** (il sorgente
condiviso con sospermesso/studiolegaleoltre è giallo/teal). Dopo una nuova build del
bundle (progetto "PATTO UE", `assemble_deploy.py`):

```bash
# 1. copia il bundle nuovo (dalla staging di sospermesso o dal deploy/ del progetto)
# 2. ritinta i CSS in blu:
npm run retheme
# 3. reinietta i meta SEO (canonical, description, Open Graph):
npm run seo
# 4. rimette il logo del sito nella topbar "torna alla home":
npm run logo
```

`scripts/retheme_blue.py` è idempotente e verifica che non restino token gialli/teal.
`scripts/seo_bundle.py` è anch'esso idempotente: aggiunge nel `<head>` di ogni pagina
del bundle canonical, meta description e tag Open Graph (blocco `<!-- seo:begin -->`);
`index.html` e `audit.html` ricevono solo `noindex`. Va rilanciato dopo OGNI ricopia
del bundle, insieme a retheme.
`scripts/inject_bundle_logo.py` è idempotente: sostituisce nella topbar il link
testuale "⌂ SOS Patto" con il logo reale (`IMAGES/logo-header.png`) cliccabile
verso la home, e aggiunge la regola `.topbar-logo` ai 5 `style.css` del bundle.
Il ROSSO delle novelle (inserimenti/soppressioni) è convenzione giuridica e non si tocca.
Aggiorna anche la data in `_data/testi.js` (`aggiornamento`).

## Come aggiornare il DIAGRAMMA

`public/diagramma/index.html` è un file unico autonomo (fonte: cartella "Diagrammone",
Corso imPATTO). Basta sostituirlo.

## Deploy (Netlify)

Collegato al repo GitHub: ogni push su `main` fa build (`npm run build`) e pubblica `_site/`.
Config in `netlify.toml`. Dominio da collegare nel pannello Netlify → Domain management.

⚠️ Il repo vive su Desktop (sincronizzato iCloud): fai `git add` mirato (mai `git commit -a`)
per non trascinare file spazzatura tipo `nome 2.ext` creati da iCloud.
