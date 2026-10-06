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
  patto-interattivo/   bundle dei testi interattivi (10 atti UE + 4 leggi coordinate + il d.l. 100/2026)
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

⚠️ Solo atti dell'amministrazione e prassi. **Decreti-legge, d.lgs. e leggi non sono circolari**:
vanno in «Normativa italiana» come testo interattivo (sotto, e `REDAZIONE.md` § 7). Il build lo
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

Il bundle vive in `public/patto-interattivo/` e **non si modifica a mano**: si ricopia
dalla sorgente e si rilanciano tre script idempotenti che lo adattano a SOS Patto.

**Sorgente**: la copia del bundle nel sito sospermesso,
`~/TECH/SOSpermesso/Sito_Nuovo/public/patto-interattivo/`. È quella (non il `deploy/`
del progetto "PATTO UE") ad avere il CSS «tema SOS Permesso» che `retheme_blue.py` sa
ritingere: il `deploy/` di PATTO UE ha un tema diverso e i suoi CSS resterebbero com'è.
A monte, il bundle nasce nel progetto "PATTO UE" (`~/Desktop/CONOSCENZA/PATTO UE/`,
`assemble_deploy.py` + un `build_dlgs*.py` per legge) e da lì passa a sospermesso.

```bash
# 1. copia il bundle nuovo (solo la cartella patto-interattivo/, mai le copie iCloud
#    tipo "patto-interattivo 2")
rsync -a ~/TECH/SOSpermesso/Sito_Nuovo/public/patto-interattivo/ public/patto-interattivo/
# 2. ritinta i CSS in blu:
npm run retheme
# 3. reinietta i meta SEO (canonical, description, Open Graph):
npm run seo
# 4. adatta il bundle al sito (logo, link home, pannello, hub, CSS della topbar):
npm run logo
# 5. controlla: devono cambiare SOLO i file il cui contenuto è davvero nuovo
git status --short public/patto-interattivo
```

Cosa fa ciascuno (tutti rieseguibili senza danni; l'ordine non conta):
- `scripts/retheme_blue.py` ritinta giallo/teal → blu nei 9 CSS del bundle e verifica
  che non restino token del tema di origine. Il ROSSO delle novelle (inserimenti e
  soppressioni) è convenzione giuridica e non si tocca.
- `scripts/seo_bundle.py` aggiunge nel `<head>` di ogni pagina canonical, meta description
  e tag Open Graph (blocco `<!-- seo:begin -->`); `index.html` e `audit.html` ricevono
  solo `noindex`.
- `scripts/inject_bundle_logo.py` fa le personalizzazioni che prima erano state fatte a
  mano e che una ricopia distruggeva: nella topbar il link testuale «⌂ Patto UE» /
  «⌂ SOS Permesso» diventa il logo del sito (`IMAGES/logo-header.png`) verso la home;
  in fondo al pannello a comparsa «⌂ Patto UE» diventa «⌂ SOS Patto» verso `/`; la hub
  `index.html` del bundle diventa un redirect a `/testi.html` (assorbita da
  `/testi.html` e `/norme-italiane.html`); aggiunge il blocco CSS `sospatto:brand` ai 5
  `style.css` e aggiorna il cache-buster `?v=` del CSS in ogni pagina.

Verificato il 14 settembre 2026: copia + tre script riproducono il bundle committato
byte per byte (esclusa la cartella `dl-100-2026/`, che non viene da sospermesso: v. sotto). Se dopo il passo 5 compaiono differenze inattese (topbar, hub, CSS), il
sorgente ha cambiato forma e va aggiornato lo script, non il bundle a mano.
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
- **Generatore** (`~/Desktop/CONOSCENZA/PATTO UE/versioni.py`, agganciato ai `build_dlgs*.py` e a
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
`versioni.py`; poi build, copia, `npm run seo && npm run logo` (sotto).

### Il d.l. 100/2026 (`public/patto-interattivo/dl-100-2026/`)

Il decreto di attuazione del Patto **non sta nella copia sospermesso**: è generato a monte, nel
progetto "PATTO UE", da `dl-100-2026-interattivo/build_dl100.py` (sorgente: lo snapshot Normattiva
`nm_fresh_20260710/dl100/`, 19 articoli; convertito senza modificazioni dalla l. 145/2026). Gli
artt. 1, 2 e 16 li ha poi modificati l'art. 7 del d.l. 7 agosto 2026, n. 144: è lo strato
`amendments_dl144.json`, generato da `genera_strato_dl144.py` confrontando lo snapshot del 10/7 con
`nm_fresh_20260929/dl100/`; quei tre articoli hanno il selettore Nuovo / Vecchio / Modifiche (l'art. 17 lo ha per il d.l. 168/2026, v. sotto). ⚠️ Il
d.l. 144 è in conversione (scade il 6/10/2026) e il testo delle Commissioni cambia il nuovo art. 16:
a conversione avvenuta, riscaricare (`fetch_normattiva.py --act dl100`) e rigenerare lo strato. È un
atto di novella, non un consolidato: viene reso come testo vigente, con i rinvii navigabili verso gli atti del Patto, i tre d.lgs.
coordinati (anche i rinvii «nudi» degli artt. 10-12 — «l'articolo 4 è sostituito…» — vanno al
d.lgs. che quel comma nòvella) e il decreto stesso. È registrato in `sites.json` del progetto
sorgente come `dl-2026-100`, così alla prossima ricostruzione anche i quattro d.lgs. lo linkano.

Per aggiornarlo: `python3 build_dl100.py` nel progetto sorgente, poi copia a mano

```bash
D=~/Desktop/CONOSCENZA/PATTO\ UE/dl-100-2026-interattivo
cp "$D/index.html" public/patto-interattivo/dl-100-2026/index.html
cp "$D/assets/data.js" "$D/assets/amend.css" public/patto-interattivo/dl-100-2026/assets/
npm run seo && npm run logo      # meta SEO, logo in topbar, «⌂ SOS Patto», cache-buster
```

`style.css` e `app.js` della cartella sono gli stessi delle quattro leggi (già ritinti e con il
blocco `sospatto:brand`): se cambiano lì, ricopiali da `dlgs-251-2007/assets/`. L'`rsync` da
sospermesso non tocca la cartella (non usa `--delete`). Le citazioni «art. 17, comma 4, d.l.
100/2026» nelle schede si linkano al testo interattivo come le altre (`scripts/norme-linker.js`,
chiave `dl-2026-100`).

### Il d.lgs. 115/2026 (`public/patto-interattivo/dlgs-115-2026/`)

Il decreto sulla tratta (attuazione della dir. (UE) 2024/1712, in vigore dal 16/7/2026) è, come il
d.l. 100, un atto di novella reso come testo vigente: modifica l'art. 18 T.U. immigrazione, l'art. 17
d.lgs. 142/2015 e l'art. 32 d.lgs. 25/2008, che lo mostrano articolo per articolo. Generato da
`dlgs-115-2026-interattivo/build_dlgs115.py`, che riusa `build_dl100.py` (sorgente:
`nm_fresh_20260929/dlgs115/`, `fetch_normattiva.py --act dlgs115`); registrato in `sites.json` come
`dlgs-2026-115`, in `scripts/norme-linker.js` (LEGGI) e in `_data/testi.js`. Copia come il d.l. 100
(index.html + assets/data.js + amend.css; style.css e app.js da `dlgs-251-2007/assets`).

### Il d.l. 168/2026 (`public/patto-interattivo/dl-168-2026/`)

D.l. 29 settembre 2026, n. 168 (G.U. n. 226, in vigore dal 30/9/2026, in conversione: scade il
28/11/2026). Per il Patto rileva l'art. 4, che novella l'art. 17 del d.l. 100/2026 (comma 1: regime
transitorio fino al 30 aprile 2027; comma 3: documento della registrazione equivalente a quello
dell'art. 4, comma 4, d.lgs. 142/2015, valido un anno, consente il lavoro). Generato da
`dl-168-2026-interattivo/build_dl168.py`, che riusa `build_dl100.py` (sorgente:
`nm_fresh_20261006/dl168/`, `fetch_normattiva.py --act dl168`); registrato in `sites.json` come
`dl-2026-168`, in `scripts/norme-linker.js` (LEGGI), in `_data/testi.js` e in `seo_bundle.py`.
Nel d.l. 100 è lo strato `amendments_dl168.json` (`genera_strato_dl168.py`, confronto fra
`nm_fresh_20260929/dl100` e `nm_fresh_20261006/dl100`): l'art. 17 ha il selettore Nuovo / Vecchio /
Modifiche. A conversione avvenuta, riscaricare `dl100` e `dl168` e rigenerare lo strato.

### Ricostruire e copiare tutto

```bash
cd ~/Desktop/CONOSCENZA/PATTO\ UE && for pass in 1 2; do for f in "Dlgs25 interattivo/build_dlgs25.py" 142-15-interattivo/build_dlgs142.py 286-98-interattivo/build_dlgs286.py 251-07-interattivo/build_dlgs251.py dl-100-2026-interattivo/build_dl100.py dlgs-115-2026-interattivo/build_dlgs115.py dl-168-2026-interattivo/build_dl168.py; do (cd "$(dirname "$f")" && python3 "$(basename "$f")" >/dev/null); done; done
```

Due passate perché ogni testo porta nelle anteprime gli articoli degli altri. Poi, da SOSPATTO,
si copiano `index.html` e `assets/data.js` di ciascuno nella sua cartella di `public/patto-interattivo/`
e si rilanciano `npm run seo && npm run logo`. ⚠️ Finché la copia sospermesso non è aggiornata
allo stesso modo, l'rsync da sospermesso del primo passo riporta indietro queste pagine.

## Come aggiornare il DIAGRAMMA

`public/diagramma/index.html` è un file unico autonomo (fonte: cartella "Diagrammone",
Corso imPATTO). Basta sostituirlo.

## Deploy (Netlify)

Collegato al repo GitHub: ogni push su `main` fa build (`npm run build`) e pubblica `_site/`.
Config in `netlify.toml`. Dominio da collegare nel pannello Netlify → Domain management.

⚠️ Il repo vive su Desktop (sincronizzato iCloud): fai `git add` mirato (mai `git commit -a`)
per non trascinare file spazzatura tipo `nome 2.ext` creati da iCloud.
