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

### Il d.l. 100/2026 (`public/patto-interattivo/dl-100-2026/`)

Il decreto di attuazione del Patto **non sta nella copia sospermesso**: è generato a monte, nel
progetto "PATTO UE", da `dl-100-2026-interattivo/build_dl100.py` (sorgente: lo snapshot Normattiva
`nm_fresh_20260710/dl100/`, 19 articoli; convertito senza modificazioni dalla l. 145/2026, quindi
ancora il testo vigente). È un atto di novella, non un consolidato: viene reso come testo vigente
senza modifiche evidenziate, con i rinvii navigabili verso gli atti del Patto, i tre d.lgs.
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

## Come aggiornare il DIAGRAMMA

`public/diagramma/index.html` è un file unico autonomo (fonte: cartella "Diagrammone",
Corso imPATTO). Basta sostituirlo.

## Deploy (Netlify)

Collegato al repo GitHub: ogni push su `main` fa build (`npm run build`) e pubblica `_site/`.
Config in `netlify.toml`. Dominio da collegare nel pannello Netlify → Domain management.

⚠️ Il repo vive su Desktop (sincronizzato iCloud): fai `git add` mirato (mai `git commit -a`)
per non trascinare file spazzatura tipo `nome 2.ext` creati da iCloud.
