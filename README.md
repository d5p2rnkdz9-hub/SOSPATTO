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
content/          giurisprudenza/, circolari/ e dottrina/ — UNA scheda = UN file .md
public/           copiato tale e quale alla radice del sito:
  patto-interattivo/   bundle dei testi interattivi (10 atti UE + 82 atti collegati + 7 leggi italiane),
                       generato da tools/testi-interattivi/ (npm run testi)
  diagramma/           Diagrammone (flowchart screening/procedure, file unico)
  allegati/            PDF di giurisprudenza e circolari
scripts/          retheme_blue.py — ritinta in blu i CSS (sito + bundle)
                  seo_bundle.py — inietta canonical/description/OG nel bundle
                  inject_bundle_logo.py — logo, link home e CSS brand nel bundle
tools/testi-interattivi/   generatori dei testi interattivi: snapshot Normattiva/EUR-Lex, builder, assemble.py
tools/kb/         build_kb.py (→ kb/, ignorata da git) e kb.py per interrogarla; ocr_cache/ locale
kb/               KB testuale generata (npm run kb): norme con tag di citazione, schede, testi dei PDF
```

## Come aggiungere una DECISIONE (giurisprudenza)

1. Copia `content/giurisprudenza/esempio-tribunale-roma-2026.md` con un nome parlante,
   es. `trib-roma-2026-06-20-frontiera.md`.
2. Compila il frontmatter: `corte`, `tipo`, `numero`, `date` (AAAA-MM-GG), `temi`,
   `massima`, `norme` (etichetta + link all'articolo nel testo interattivo,
   es. `/patto-interattivo/1348.html` o `/patto-interattivo/dlgs-25-2008/index.html#art_32`).
   Togli `esempio: true`.
3. (Facoltativo) PDF del provvedimento **anonimizzato** in `public/allegati/giurisprudenza/`
   e percorso nel campo `pdf`. **NON basta disegnare un rettangolo nero**: se è
   semitrasparente o lascia sotto testo/immagine, il dato resta leggibile. Usa lo
   script che fa redaction VERA e irreversibile (rimuove pixel e testo):

   ```bash
   # scansione con box semitrasparenti già presenti + sweep OCR su nomi/date:
   python3 scripts/oscura_pdf.py SORGENTE.pdf \
       public/allegati/giurisprudenza/<nomefile>.pdf \
       --riscura --ocr --nomi "COGNOME Nome" "Luogo di nascita" --verifica
   ```

   ⚠️ **Verifica sempre**: `--verifica` genera le anteprime in
   `<out>.pdf_verifica/` e azzera il testo estraibile, ma l'auto-rilevamento non
   garantisce da solo (un dato mai coperto — es. un anno di nascita nudo fuori dai
   box — può restare visibile). Guarda le anteprime e, per ogni residuo, aggiungi
   `--box PAGINA:x0,y0,x1,y1` (coordinate in punti). La cartella `_verifica/` è
   solo di lavoro: non committarla.

   **Cosa lo script oscura SEMPRE** (`PATTERNS_SEMPRE`, non disattivabili nemmeno
   con `--solo-nomi`): **C.U.I.** — con e senza etichetta, es. `(CUI: 07J37ZV)` —
   codice fiscale, email, telefono, **data di nascita** (solo quando preceduta dal
   contesto «nato/nata … il», così le date della decisione restano leggibili) e gli
   ID dei gestionali negli URL. Sono gli identificativi che non servono mai al
   lettore della scheda ed erano la causa più frequente di ripubblicazioni: il
   C.U.I. in chiaro accanto al nome coperto è passato tre volte (Palermo 8694,
   Firenze 9251-1/2026, Bologna 12435-1/2026). Il ricontrollo che nessuno di questi
   sia più estraibile **gira sempre**, anche senza `--verifica`.

   Due avvertenze che vengono dall'uso:
   - **Sulle scansioni** (PDF senza livello testo) il ricontrollo automatico dice
     sempre «0 caratteri»: il dato sta nei pixel, non è estraibile e quindi non
     viene segnalato, ma è perfettamente leggibile. **Lì l'unica verifica che vale è
     guardare le anteprime.**
   - `--riscura --ocr` su una scansione di provvedimento oscura *tutte* le date, e
     su questi decreti le date sono la sostanza (ingresso, manifestazione di
     volontà, C3, data del decreto). Aggiungi **`--solo-nomi` anche con `--ocr`**:
     l'OCR continua a cercare C.U.I./codici/email/telefoni ma lascia stare le date,
     e per l'eventuale data di nascita usi un `--box` mirato.
4. Il corpo del file è il commento libero in Markdown. Le citazioni normative — «art. 42,
   par. 1, lett. j) Reg. (UE) 2024/1348», «art. 35-bis, comma 3, d.lgs. 25/2008» — diventano
   in build link al testo interattivo con anteprima al passaggio del mouse (come gli `xref`
   del bundle): **non servono link a mano**, basta la forma canonica. Le citazioni senza atto
   («l'art. 43, par. 1, richiama…») si risolvono sul contesto del paragrafo; per le ambigue
   rendi esplicito l'atto. `npm run norme-check` elenca ciò che non risolve e perché
   (dettagli e grammatica in `scripts/norme-linker.js`).
5. `git add … && git commit && git push` → Netlify ricostruisce e pubblica da solo.

> Le bozze non ancora pronte (es. PDF da rioscurare) usano l'estensione
> `.md.bozza`: Eleventy le ignora finché non le rinomini in `.md`.

La scheda appare automaticamente in `/giurisprudenza.html` (ordinata per data
decrescente) e ha la sua pagina `/giurisprudenza/<nomefile>.html`.

## Come aggiungere una CIRCOLARE

Identico, in `content/circolari/` (campi: `ente`, `tipo`, `numero`, `date`, `temi`,
`oggetto`, `norme`, `pdf`). PDF in `public/allegati/circolari/`.

⚠️ Solo atti dell'amministrazione e prassi. **Decreti-legge, d.lgs., leggi e D.M. non sono
circolari**: vanno in «Normativa italiana», come testo interattivo (sotto) o, se non ce l'hanno,
come scheda in `content/normativa/` con la card in `_data/testi.js` (`REDAZIONE.md` § 7). Il build lo
controlla (`scripts/check_collocazione.js`).

## Come aggiungere un contributo di DOTTRINA

Un file .md in `content/dottrina/` (nome parlante: `autore-argomento-AAAA-MM.md`).
Campi del frontmatter: `fonte` (rivista/occasione, appare come kicker), `titolo`,
`autori`, `date` (AAAA-MM-GG, serve solo per l'ordinamento), `temi` (stesse label
canoniche di `_data/vocabolarioTemi.js`, su UNA riga: `temi: [Tema uno, Tema due]`),
`sommario` (2-5 righe) e `links` (uno o più pulsanti; `interna: true` per i link
interni al sito, che non aprono una nuova scheda):

```yaml
links:
  - { label: "↗ Leggi l'articolo", href: "https://..." }
  - { label: "📄 Scarica il contributo (PDF)", href: "/allegati/circolari/... .pdf" }
```

Le schede non hanno pagina di dettaglio (`permalink: false`): compaiono solo
nell'elenco `/dottrina.html`, filtrabile per tema come giurisprudenza e circolari.
I temi sulla card rimandano alla giurisprudenza sullo stesso tema
(`/giurisprudenza.html?tema=<slug>`). `npm run temi-check` verifica anche queste.

## Come aggiornare i TESTI INTERATTIVI

Il bundle vive in `public/patto-interattivo/` e **non si modifica a mano**: lo generano gli
script di `tools/testi-interattivi/`, che da ottobre 2026 stanno in questo repo (prima nel
progetto privato "PATTO UE" su Desktop, con passaggio dalla copia di sospermesso: quel giro è
finito, SOSPATTO è autonomo). Dentro `tools/testi-interattivi/`:

```
sites.json                        registro dei testi (slug nel bundle, cartella sorgente, date, etichette)
versioni.py                       strati di modifica per atto → selettore Nuovo / Vecchio / Modifiche
fetch_normattiva.py               scarica da Normattiva uno snapshot datato (nm_fresh_AAAAMMGG/)
confronto_normattiva.py           confronta uno snapshot col testo generato (+ confronto_whitelist.json)
nm_html*/ , nm_fresh_*/           snapshot Normattiva congelati: sono LA fonte dei testi italiani
D.Lgs_*.akn.xml                   Akoma Ntoso dei quattro d.lgs. (metadati per i builder)
Dlgs25 interattivo/ 142-15-… 286-98-… 251-07-…   un builder per legge coordinata
                                  (build_dlgs*.py, amendments.json, overrides.json, extra_acts.json)
dl-100-2026-interattivo/          build_dl100.py + strati amendments_dl144/dl168.json (genera_strato_*.py)
dlgs-115-2026-interattivo/ , dl-168-2026-interattivo/   riusano build_dl100.py
Testi definitivi Regolamenti/     build_patto_interattivo.py: i 10 atti del Patto dagli HTML EUR-Lex
                                  (TEsti html/) + gli 82 atti esterni (Atti esterni html/, scarica_atti_esterni.py)
assemble.py                       compone public/patto-interattivo/ (sotto)
```

Gli output dei builder (`index.html`, `assets/data.js`, `assets/amend.css`, `assets/data-ext/`,
`REPORT_MODIFICHE.md`, le pagine in `Patto interattivo/`) sono in `.gitignore`: si rigenerano.
Dipendenze: `python3` con `bs4`.

```bash
npm run testi          # build Patto (12 s) + due passate delle leggi + copia + retheme + seo + logo
npm run testi-copia    # solo copia + adattamento, se gli output sono già pronti
git status --short public/patto-interattivo   # devono cambiare SOLO i file col contenuto davvero nuovo
```

Cosa fa `assemble.py`: ricostruisce tutto (due passate perché ogni testo porta nelle anteprime
gli articoli degli altri), poi copia nel bundle **solo i file di contenuto**: per il Patto le
pagine `<num>.html`, `ext-*.html`, `audit.html`, `assets/data.js` e `assets/data-ext/`; per
ogni legge `<slug>/index.html`, `assets/data.js`, `assets/amend.css`, `assets/data-ext/`. Alle
pagine del Patto aggiunge la breadcrumb «⌂ Patto UE › atto» e il link al Patto nel pannello.
**`style.css` e `app.js` del bundle non li tocca**: sono di SOS Patto (tema blu, blocco
`sospatto:brand`), i builder portano ancora il tema di origine. La hub `index.html` del bundle
è un redirect a `/testi.html` e non viene sovrascritta.

I tre script di adattamento restano quelli di prima, idempotenti e in qualunque ordine:
- `scripts/retheme_blue.py` ritinta giallo/teal → blu nei CSS del bundle e verifica che non
  restino token del tema di origine. Il ROSSO delle novelle è convenzione giuridica e non si tocca.
- `scripts/seo_bundle.py` aggiunge nel `<head>` di ogni pagina canonical, meta description e
  tag Open Graph (blocco `<!-- seo:begin -->`); `index.html` e `audit.html` ricevono solo `noindex`.
- `scripts/inject_bundle_logo.py`: nella topbar il link «⌂ Patto UE» diventa il logo del sito
  verso la home; in fondo al pannello «⌂ Patto UE» diventa «⌂ SOS Patto» verso `/`; la hub
  diventa il redirect; aggiunge il blocco CSS `sospatto:brand` agli `style.css` e aggiorna il
  cache-buster `?v=` del CSS in ogni pagina.

Verificato il 7 ottobre 2026: `npm run testi-copia` sul bundle committato cambia solo i 4
`amend.css` delle leggi coordinate (colori allineati a quelli di dl-100/dlgs-115/dl-168, che
già venivano dal builder). Se compaiono differenze inattese (topbar, hub, CSS), il builder ha
cambiato forma e va aggiornato `assemble.py` o lo script di adattamento, non il bundle a mano.
Aggiorna anche la data in `_data/testi.js` (`aggiornamento`) quando cambia il testo delle norme.

### Versioni degli articoli: Nuovo / Vecchio / Modifiche

Ogni articolo modificato di recente ha, sotto la rubrica, la riga «Modificato dal d.l. 12 giugno
2026, n. 100 (art. 11); poi modificato dal d.lgs. 12 giugno 2026, n. 115 (art. 11)» e un
selettore solo per quell'articolo: **Nuovo** (testo in vigore, default), **Vecchio** (la versione
**immediatamente precedente l'ultima modifica** di quell'articolo) e **Modifiche** (le differenze
tra le due, barrato + evidenziato). Una barra sotto il banner imposta tutti gli articoli in un
colpo; la scelta è ricordata (`localStorage`) e linkabile: `…/dlgs-25-2008/?v=vecchio#art_28-bis`
(valgono anche i vecchi `?v=vigente|previgente|confronto`). Un'ancora verso testo che la vista
dell'articolo non ha (es. `#art_26-bis` in Vecchio) apre quell'articolo sulle Modifiche e lo dice.
Vale per le tre leggi coordinate e per il d.l. 100/2026 (artt. 1, 2, 16).

Cosa viene da dove:
- **Generatore** (`tools/testi-interattivi/versioni.py`, agganciato ai `build_dlgs*.py` e a
  `build_dl100.py`): le modifiche a **strati per atto** — le voci di `amendments.json` si
  raggruppano per l'atto nominato in `src` («…, d.lgs. 115/2026»; senza `src` = d.l. 100), più
  eventuali `amendments_<atto>.json`, e si applicano in ordine di entrata in vigore; ogni articolo
  toccato da uno strato mostra il confronto con lo strato prima. Poi la riga «Modificato dal …»
  (`p.amd-storia`, `data-ultima` sul `<div>`) e i **rinvii per versione**: ogni link del testo
  vecchio porta all'atto del testo vecchio («regolamento (UE) ~~n. 604/2013~~ 2024/1351»: 604/2013
  nel Vecchio, 2024/1351 nel Nuovo), con `data-alt` / `data-v` sui pezzi comuni.
- **Sito**: bottoni, barra e comportamento li aggiunge la build (`eleventy.config.mjs` →
  `scripts/versioni-inject.js`) alle copie in `_site/`, e il `npm run dev` al volo, solo sulle
  pagine con `amd-storia`: una ricopia del bundle non li cancella. Lato browser:
  `src/scripts/versioni-testo.js` + `src/styles/versioni-testo.css`.

Una nuova modifica legislativa a una delle leggi: si aggiungono le sue voci ad `amendments.json`
del builder (op come le altre, `src` che finisce con l'atto, es. «art. 8, comma 1, lettera a),
d.lgs. 115/2026») e l'atto con la data di entrata in vigore in `ACT_NAMES` / `ACT_DATES` di
`versioni.py`; poi `npm run testi`.

### Il d.l. 100/2026, il d.lgs. 115/2026 e il d.l. 168/2026

Sono atti di novella resi come testo vigente, con i rinvii navigabili verso gli atti del Patto,
i d.lgs. coordinati e sé stessi; i rinvii «nudi» degli artt. 10-12 del d.l. 100 («l'articolo 4 è
sostituito…») vanno al d.lgs. che quel comma nòvella.
- **d.l. 100/2026** (`dl-100-2026-interattivo/build_dl100.py`, fonte `nm_fresh_20260710/dl100/`,
  19 articoli; convertito senza modificazioni dalla l. 145/2026). Gli artt. 1, 2 e 16 li ha
  modificati l'art. 7 del d.l. 144/2026 (strato `amendments_dl144.json`, da `genera_strato_dl144.py`
  confrontando lo snapshot del 10/7 con `nm_fresh_20260929/dl100/`); l'art. 17 l'art. 4 del
  d.l. 168/2026 (strato `amendments_dl168.json`, `genera_strato_dl168.py`, snapshot 29/9 vs 6/10).
  ⚠️ A conversione dei d.l. 144 e 168, riscaricare (`fetch_normattiva.py --act dl100`) e
  rigenerare gli strati.
- **d.lgs. 115/2026** (tratta, attuazione della dir. (UE) 2024/1712, in vigore dal 16/7/2026):
  `dlgs-115-2026-interattivo/build_dlgs115.py`, fonte `nm_fresh_20260929/dlgs115/`. Modifica
  l'art. 18 T.U., l'art. 17 d.lgs. 142/2015 e l'art. 32 d.lgs. 25/2008, che lo mostrano
  articolo per articolo.
- **d.l. 168/2026** (G.U. n. 226, in vigore dal 30/9/2026, in conversione: scade il 28/11/2026):
  `dl-168-2026-interattivo/build_dl168.py`, fonte `nm_fresh_20261006/dl168/`. L'art. 4 novella
  l'art. 17 del d.l. 100 (regime transitorio fino al 30 aprile 2027; documento della
  registrazione valido un anno, consente il lavoro).

Ognuno è registrato in `sites.json` (`dl-2026-100`, `dlgs-2026-115`, `dl-2026-168`), in
`scripts/norme-linker.js` (LEGGI), in `_data/testi.js` e in `scripts/seo_bundle.py`. Un nuovo
atto: cartella `<slug>-interattivo/` con un `build_*.py` che riusa `build_dl100.py`, voce in
`sites.json` e nei quattro registri qui sopra, poi `npm run testi` (`assemble.py` crea la
cartella nel bundle e le dà `style.css` e `app.js` di `dlgs-251-2007`).

### Nuovo snapshot Normattiva

```bash
cd tools/testi-interattivi
python3 fetch_normattiva.py --act dl100            # → nm_fresh_AAAAMMGG/dl100/
python3 confronto_normattiva.py --act dlgs25 --freshdir nm_fresh_AAAAMMGG   # cosa è cambiato
```

I builder leggono gli snapshot indicati nel loro `SRC` (le quattro leggi: `nm_html*`, con le
modifiche applicate da `amendments.json`; i decreti del 2026: `nm_fresh_*`). Un testo cambiato
su Normattiva diventa o uno strato in `amendments*.json` (se è una novella da mostrare con
Nuovo / Vecchio / Modifiche) o un nuovo `SRC`.

## Come aggiornare il DIAGRAMMA

`public/diagramma/index.html` è un file unico autonomo (fonte: cartella "Diagrammone",
Corso imPATTO). Basta sostituirlo.

## KB testuale e chatbot

`npm run kb` (= `tools/kb/build_kb.py`) genera in `kb/` la knowledge base testuale di tutto ciò che
è pubblicato: norme UE e italiane riga per riga con il tag di citazione (`[1348 art.13 par.8]`,
`[dlgs25 art.35-bis c.3]`), atti collegati, schede di giurisprudenza, circolari, normativa e
dottrina con il testo integrale dei PDF (OCR dove serve, cache in `tools/kb/ocr_cache/`).
`kb/` è in `.gitignore`: si rigenera in ~10 s dal working tree; la cache OCR è locale e va
conservata. Si interroga con `tools/kb/kb.py` (`cerca`, `art`, `cons`, `giur`, `schede`); è la
base della skill `ricerca-kb-sospatto`. Struttura e comandi in `tools/kb/README.md`.

`npm run chatbot-kb` (= `scripts/chatbot-kb.mjs`) ricava dalla KB i tre JSON di `netlify/chat/kb/`
letti dalla funzione del chatbot (`netlify/chat/core.mjs`). Sequenza dopo una modifica al sito:
`npm run build && npm run kb && npm run chatbot-kb`.

## Deploy (Netlify)

Collegato al repo GitHub: ogni push su `main` fa build (`npm run build`) e pubblica `_site/`.
Config in `netlify.toml`. Dominio da collegare nel pannello Netlify → Domain management.

⚠️ `git add` mirato (mai `git commit -a`): `Materiali da caricare SOSPATTO/` contiene PDF non
oscurati ed è ignorata, ma file di lavoro e duplicati tipo `nome 2.ext` non devono finire nel repo pubblico.
