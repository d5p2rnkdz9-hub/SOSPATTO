# KB SOS Patto

Knowledge base testuale di tutto ciò che è pubblicato su www.sospatto.it, in markdown pensato per `grep`/`kb.py`.
Vive in `kb/` alla radice del repo (in `.gitignore`: si rigenera con `npm run kb`, ~10 s): **non modificare a mano i file generati**.
Gli script stanno qui in `tools/kb/`; la cache OCR in `tools/kb/ocr_cache/` (ignorata da git, ma da conservare: l'OCR è la parte lenta).
Dalla KB `node scripts/chatbot-kb.mjs` (`npm run chatbot-kb`) genera `netlify/chat/kb/` per il chatbot.

| Cartella | Contenuto | Tag di citazione per riga |
|---|---|---|
| `1-norme-ue/` | 10 atti del Patto (dir. 1346, reg. 1347–1359), testo EUR-Lex, considerando e allegati | `[1348 art.13 par.8 lett.a]`, `[1348 cons.27]`, `[1348 all.1]` |
| `2-norme-italiane/` | d.l. 100/2026; d.lgs. 25/2008, 142/2015, 286/1998 coordinati col d.l. 100; d.lgs. 251/2007 | `[dlgs25 art.35-bis c.3 lett.a]`; testo ante-novella: `[… PREVIGENTE]`; commi modificati: `⟨novella: …⟩` |
| `2-normativa-schede/` | schede di atti normativi italiani senza testo interattivo (D.M. zone di frontiera…): metadati, oggetto, commento, testo del PDF | — |
| `3-giurisprudenza/` | una scheda per decisione: metadati, massima e commento **redazionali**, poi testo integrale dal PDF oscurato con `[p. N]` (OCR segnalato) | — (citare corte, tipo, numero, data, pagina) |
| `4-circolari-prassi/` | circolari, decreti, prassi amministrative + testo dei PDF e allegati | — |
| `5-dottrina/` | schede di dottrina (sommari; testo integrale solo se il PDF è sul sito) + trascrizione audizione Perilli | — |
| `6-atti-collegati/` | 82 atti UE richiamati dal Patto (dir. 2008/115, 2011/36, reg. 604/2013, Schengen…) | `[dir-2011-36 art.2 par.1]` |
| `INDICE-norme-citate.md` | indice inverso norma → schede che la richiamano (campo `norme`) | |
| `CATALOGO.md` | elenco di tutti i file, data di build e commit del sito | |

Sottotipi dei tag: `par` paragrafo UE, `c` comma italiano, `lett` lettera, `n` punto numerato (definizioni), `pt` punto romano/sotto-lettera, `tratt` trattino.

## Ricerca

```
tools/kb/kb.py cerca '\btratta\b|2011/36' -s norme      # righe con tag + tabella di COPERTURA per atto
tools/kb/kb.py cerca 'formalizzat' -s giur -C           # con righe di contesto
tools/kb/kb.py art 1348 13 8                             # art. 13 par. 8 reg. procedure
tools/kb/kb.py art dlgs25 35-bis                         # articolo intero (vigente + previgente)
tools/kb/kb.py cons 1348 27                              # considerando
tools/kb/kb.py giur 1348 79                              # decisioni/circolari che citano la norma
tools/kb/kb.py schede -s giur -t trattenimento           # elenco schede per tema
```
La ricerca ignora maiuscole, accenti e l'apostrofo di Normattiva (`puo'` = `può`). Usare `\b` per le parole brevi.

## Aggiornamento

```
npm run kb
```
Legge il working tree del sito (esclude `.md.bozza` ed `esempio: true`), rifà tutto in ~10 s; l'OCR (tesseract ita, 300 dpi) gira solo sui PDF nuovi — cache in `tools/kb/ocr_cache/<md5>.json`.
Dipendenze: python3 con `bs4`, `pyyaml`, `pymupdf`; `pdftoppm`, `tesseract` (lingua ita).
