# Traduzioni EN / FR — regole operative

SOS Patto è in italiano (radice del sito) con versioni **inglese** (`/en/…`) e **francese**
(`/fr/…`). Il selettore a bandierina nel menu porta alla stessa pagina nell'altra lingua, o alla
home di quella lingua se la pagina non è tradotta.

## Che cosa si traduce e che cosa no

| si traduce | resta in italiano |
|---|---|
| interfaccia (menu, footer, nastro, etichette delle schede) — `_data/i18n.js`, `nav.js`, `updates.js`, `testi.js` | i provvedimenti e i documenti originali (PDF in `public/allegati/`) |
| pagine del sito (`en/pages/`, `fr/pages/`, `en/index.html`, `fr/index.html`) | i testi interattivi di leggi e regolamenti (`public/patto-interattivo/`) |
| **schede** di giurisprudenza e circolari (frontmatter testuale + commento) | il diagramma (`/diagramma.html`) e l'audizione Perilli |
| sommari della dottrina | titoli e fonte dei contributi di dottrina |

## Dove stanno i file

Una traduzione = un file con **lo stesso nome** dell'originale:

```
content/giurisprudenza/trib-venezia-13622-2026-09-22.md        (IT, fonte)
content/en/giurisprudenza/trib-venezia-13622-2026-09-22.md     → /en/giurisprudenza/trib-venezia-13622-2026-09-22.html
content/fr/giurisprudenza/trib-venezia-13622-2026-09-22.md     → /fr/giurisprudenza/…
```

Idem `content/{en,fr}/circolari/` e `content/{en,fr}/dottrina/`. Le bozze (`.md.bozza`) non si
traducono finché non sono pubblicate.

## Frontmatter

Il file tradotto ripete **tutto** il frontmatter dell'originale, nello stesso ordine:

- **identici, copiati tali e quali**: `corte`, `numero`, `date`, `temi` (label italiane: la
  traduzione la fa il sito), `pdf`, tutti gli `href` (di `norme`, `allegati`, `links`),
  `norme_impliciti`, `esempio`, e per la dottrina `titolo`, `autori`;
- **tradotti**: `tipo`, `massima`, `oggetto`, `ente`, `pdfLabel`, ogni `label` di `norme` /
  `allegati` / `links`, e per la dottrina `sommario` e la data dentro `fonte` (il nome della
  rivista resta com'è: «Questione Giustizia, Leggi e istituzioni · 29 September 2026»);
- **in più**, in testa: `it_hash: <hash>` — l'impronta del file italiano al momento della
  traduzione. Non si scrive a mano: `npm run traduzioni -- --stamp <file tradotto>`.
  Se poi l'italiano cambia, `npm run traduzioni` segnala la traduzione come da aggiornare.

## Corpo della scheda

- Traduzione integrale e fedele del commento, stessi titoli `##`, stessa misura. Registro
  giuridico formale: il lettore è un giurista. In francese, *vous*.
- Le citazioni testuali del provvedimento («…») si traducono, restando fra virgolette
  (EN “…”, FR « … »). Non aggiungere note del traduttore.
- **Link interni**: `/giurisprudenza/x.html` → `/en/giurisprudenza/x.html` (o `/fr/…`), idem
  `/circolari/` e le pagine (`/giurisprudenza.html` → `/en/giurisprudenza.html`).
  Restano invariati `/patto-interattivo/…`, `/allegati/…`, `/diagramma.html` e i link esterni.
- Nomi propri di giudici, parti, uffici: invariati.

## Citazioni normative (diventano link automatici)

Il linker riconosce queste forme; nel corpo **nessun link a mano** alle norme. Seguono lo stile
ufficiale delle versioni EN/FR della Gazzetta UE.

| italiano | English | français |
|---|---|---|
| art. 42, par. 1, lett. j) Reg. (UE) 2024/1348 | Article 42(1), point (j), of Regulation (EU) 2024/1348 | article 42, paragraphe 1, point j), du règlement (UE) 2024/1348 |
| artt. 20, 21 e 53 Reg. (UE) 2024/1348 | Articles 20, 21 and 53 of Regulation (EU) 2024/1348 | articles 20, 21 et 53 du règlement (UE) 2024/1348 |
| considerando 17 Reg. (UE) 2024/1348 | recital 17 of Regulation (EU) 2024/1348 | considérant 17 du règlement (UE) 2024/1348 |
| Dir. (UE) 2024/1346 · direttiva 2013/32/UE | Directive (EU) 2024/1346 · Directive 2013/32/EU | directive (UE) 2024/1346 · directive 2013/32/UE |
| art. 35-bis, comma 3, d.lgs. 25/2008 | Article 35-bis(3) of Legislative Decree 25/2008 | article 35-bis, alinéa 3, du décret législatif 25/2008 |
| art. 4, comma 4, lett. b) d.lgs. 142/2015 | Article 4(4)(b) of Legislative Decree 142/2015 | article 4, alinéa 4, lettre b), du décret législatif 142/2015 |
| d.l. 100/2026 | Decree-Law 100/2026 | décret-loi 100/2026 |
| d.lgs. 286/1998 (t.u. immigrazione) | Legislative Decree 286/1998 (Consolidated Immigration Act) | décret législatif 286/1998 (texte unique sur l'immigration) |
| art. 43, par. 1 (atto già citato nel paragrafo) | Article 43(1) | article 43, paragraphe 1 |

Stessa regola dell'italiano: **cita l'atto la prima volta in ogni paragrafo**. Restano testo
(e va bene): c.p.c. (*Code of Civil Procedure* / *code de procédure civile*), Costituzione, CEDU
(*ECHR* / *CEDH*), Carta (*Charter* / *Charte*), d.m., atti senza testo interattivo.
Controllo: `npm run norme-check` (0 citazioni non risolte, 0 href rotti) anche sulle traduzioni.

## Glossario

Termini tecnici del Patto: si usa **il termine della versione ufficiale EN/FR del regolamento**.

| italiano | English | français |
|---|---|---|
| domanda fatta / registrata / formalizzata | application made / registered / lodged | demande présentée / enregistrée / introduite |
| manifestazione di volontà | expression of the wish to apply | manifestation de la volonté de demander |
| procedura di frontiera | border procedure | procédure à la frontière |
| procedura accelerata | accelerated examination procedure | procédure d'examen accélérée |
| paese di origine sicuro · paese terzo sicuro | safe country of origin · safe third country | pays d'origine sûr · pays tiers sûr |
| accertamenti preliminari (screening) | screening | filtrage |
| trattenimento | detention | rétention |
| obbligo di soggiorno / di dimora | obligation to reside | obligation de résider |
| domanda reiterata | subsequent application | demande ultérieure |
| diritto di rimanere | right to remain | droit de rester |
| finzione di non ingresso | legal fiction of non-entry | fiction juridique de non-entrée |
| esigenze procedurali particolari | special procedural guarantees / needs | besoins procéduraux particuliers |
| orientamento legale gratuito | free legal counselling | conseils juridiques gratuits |
| convalida (del trattenimento) | validation (judicial review) | validation |
| rito / rito previgente | procedure / former procedural rules | procédure / règles de procédure antérieures |
| sospensiva, istanza cautelare | request for suspensive effect / interim relief | demande d'effet suspensif / mesure provisoire |
| decreto (del Tribunale) | decree | décret |
| protezione speciale | special protection (*protezione speciale*) | protection spéciale |
| sezione feriale | vacation section | section de vacation |
| Prefetto / Prefettura | Prefect / *Prefettura* | préfet / *Prefettura* |
| Sezioni Unite | Joint Chambers (Sezioni Unite) of the Court of Cassation | chambres réunies (Sezioni Unite) de la Cour de cassation |

**Restano in italiano** (in corsivo la prima volta, con una glossa breve fra parentesi se serve):
Questura, Questore, Prefettura, Commissione territoriale, C3, C.U.I., hotspot, CPR, CAS, SAI.

**Autorità**: il campo `corte` resta in italiano nel frontmatter; il sito lo mostra tradotto
tramite `_data/i18n.js` (`corti`). Se compare un ufficio nuovo, aggiungilo lì.
Città: EN Milan, Venice, Florence, Genoa, Turin, Naples, Rome · FR Milan, Venise, Florence,
Gênes, Turin, Naples, Rome, Bologne, Palerme, Messine, Pérouse, Trieste.

## Controlli prima di consegnare

```bash
npm run traduzioni     # manca qualcosa? traduzioni ferme a un italiano vecchio? campi tecnici divergenti?
npm run build
npm run norme-check
```
