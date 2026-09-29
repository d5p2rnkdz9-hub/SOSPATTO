# Piano di lavoro — SOS Patto in inglese e francese

Obiettivo: versioni **EN** e **FR** del sito con selettore di lingua a bandierina come su
SOS Permesso, senza toccare l'italiano (che resta alla radice e resta la fonte).

## Come fa SOS Permesso (e cosa non copiare)

- Italiano alla radice, altre lingue sotto `/{lang}/` **con lo stesso slug**
  (`/chi-siamo.html` → `/en/chi-siamo.html`); lingua dichiarata in front matter (`lang: en`).
- Dati per lingua: `nav[lang] | default: nav.it`, idem footer e updates (SOS Patto è già
  predisposto così per nav e banner).
- Selettore: ultima voce del menu su desktop (`nav.liquid`) + pulsante nell'header su mobile
  (`language-switcher.liquid`), bandiere **SVG** in `IMAGES/flags/` (le emoji non si vedono
  su Windows). Pagine senza traduzione: `langSwitchPath` / `langSwitchAvailable` mandano a
  una pagina di ripiego.
- `hreflang` + `x-default` in `base.liquid`, sitemap per lingua con alternates.
- Traduzioni fatte con **sub-agenti Claude Code, niente API a pagamento**, glossario
  condiviso in `SOSpermesso/translations-shared/` (termini da non tradurre: Questura,
  Commissione territoriale…).

Da **non** copiare: la logica dei prefissi scritta a mano per ogni lingua (~150 righe
ripetute in `nav.liquid` e `base.liquid`), le sitemap incomplete, i blocchi `ignores`
duplicati per lingua. Qui la calcoliamo **una volta** in un `eleventyComputed` globale
(`langUrls`: per ogni pagina l'URL nelle tre lingue, o `null` se non tradotta) e la
usano selettore, hreflang e sitemap.

## Fasi

### Fase 0 — Infrastruttura (nessun testo tradotto ancora)
1. `_data/i18n.js`: lingue (`it`, `en`, `fr`), etichette, bandiere, e le ~150 stringhe
   dell'interfaccia (layout schede: «Massima», «Norme collegate», «Scarica il
   provvedimento», breadcrumb; filtri: «Tutti», «Filtra per autorità»; footer; JS:
   anteprima norme, avvisi di connessione).
2. Filtro data per lingua (`dataIt` → `data` con `Intl.DateTimeFormat`).
3. `vocabolarioTemi.js`: `label` diventa `{it, en, fr}` con lo slug come chiave stabile;
   le schede continuano a usare la label italiana, `temi-check` invariato.
4. Footer: oggi è italiano fisso e ignora `_data/footer.js` → collegarlo.
5. Selettore a bandierina (desktop + mobile), bandiere `it`/`gb`/`fr` copiate da SOS
   Permesso; `hreflang`, `<html lang>`, `inLanguage` JSON-LD dinamici; sitemap con
   alternates.
6. Ripiego: se una pagina non ha traduzione, la bandiera porta alla pagina italiana con
   un avviso «This page is available in Italian only».

### Fase 1 — Menu, home e pagine fisse (~3.000 parole)
`index`, `testi`, `norme-italiane`, `circolari`, `giurisprudenza`,
`giurisprudenza-europea`, `dottrina`, `diagramma` (solo la cornice), `il-progetto`,
`privacy-policy`, più `nav`, `updates`, `testi.js`. L'audizione Perilli resta in
italiano (è un verbale).
**Qui si può già andare online**: sito navigabile in EN/FR, schede in italiano.

### Fase 2 — Testi interattivi (il pezzo più grosso)
- **Atti UE (10 + 82 atti esterni)**: *non si traducono*, si usano i testi ufficiali
  EN/FR di EUR-Lex. Il builder a monte (`~/Desktop/CONOSCENZA/PATTO UE/…/
  build_patto_interattivo.py`) oggi legge solo i CONVEX italiani e ha `lang="it"` e
  `legal-content/IT/` scritti nel codice: va parametrizzato per lingua, verificato il
  parsing di «Article»/«considérant», e generati `/en/patto-interattivo/` e
  `/fr/patto-interattivo/` con gli stessi anchor (`art_42`, `042.001`, `rct_17`).
  Attenzione alla regola del [bundle personalizzato]: patch file per file, mai rsync.
- **Leggi italiane** (d.lgs. 25/2008, 142/2015, 251/2007, 286/1998, d.l. 100/2026):
  non esiste testo ufficiale EN/FR → vedi decisione B.

### Fase 3 — Schede (50 decisioni, 16 circolari, 21 dottrina; ~48.000 parole)
- File paralleli con lo stesso nome: `content/en/giurisprudenza/<slug>.md`, ecc.
  Front matter tecnico (date, pdf, temi, norme href) ereditato dall'italiano via data
  cascade, così nella versione tradotta si scrive solo testo.
- Ordine: prima metadati + massima (utili subito agli elenchi filtrabili), poi i corpi.
- **norme-linker**: oggi riconosce solo citazioni italiane. Estendere la grammatica a
  «Article 42(1)(j) of Regulation (EU) 2024/1348» e «article 42, paragraphe 1, point j),
  du règlement (UE) 2024/1348», puntando al bundle della stessa lingua.
- Dottrina: titolo e fonte restano originali, si traduce il sommario.
- Script `npm run traduzioni`: elenca schede senza traduzione o con italiano modificato
  dopo la traduzione (confronto hash), da far girare nella revisione settimanale.

### Fase 4 — Diagramma
Le etichette del flowchart sono tracciati vettoriali (export Miro→SVG): non si traducono
nel file, serve una lavagna Miro tradotta e un nuovo export. Traducibili subito i 40
tooltip (`NODES`, ~1.000 parole) da `Corso imPATTO/Diagrammone/`.

## Flusso di traduzione
Sub-agenti Claude Code con glossario condiviso (riusare `translations-shared/` di SOS
Permesso ed estenderlo col lessico del Patto: *screening*, *procedura di frontiera* →
*border procedure* / *procédure à la frontière*, termini ufficiali presi dai testi UE
EN/FR). Revisione a campione di un madrelingua giurista per le massime.

## Decisioni prese (29.09.2026)

- **Fase 0 + pagine fisse + schede**: fatte. Le regole operative sono in `TRADUZIONI.md`.
- **Si traducono solo le schede** (massima, metadati, commento) e i sommari della dottrina;
  i provvedimenti originali (PDF) restano in italiano.
- **Leggi, regolamenti (testi interattivi) e diagramma: non si toccano.** Le fasi 2 e 4 sono
  quindi accantonate; dalle pagine EN/FR i link portano ai testi italiani con l'avviso «(in Italian)».
- **Nuove schede**: la routine settimanale `scraper-patto` le traduce subito, nello stesso giro,
  con sub-agenti Sonnet (`npm run traduzioni` deve dare 0 da sistemare).
