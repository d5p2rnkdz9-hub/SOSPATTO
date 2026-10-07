# Triage discrepanze — confronto con Normattiva del 10/7/2026

Fonte di verità: Normattiva (testo vigente al 10/7/2026). Gate: d.l. 100/2026
consolidato per 25/142/286; d.lgs. 251 conforme senza findings.

## Contesto scoperto durante la verifica

- **D.l. 100/2026 NON ancora convertito** (nessuna legge di conversione su
  Normattiva; artt. 10/11/12 vigenti = GU originaria, salvo tipografia).
  Banner «in corso di conversione» dei siti: ancora corretti.
- **NOVITÀ: d.lgs. 12 giugno 2026, n. 115** (GU 1/7/2026 n. 150, **in vigore
  16/7/2026**) modifica art. 32 c. 3-bis d.lgs. 25 (art. 11 c. 2), art. 17
  d.lgs. 142 e art. 18 d.lgs. 286 (materia: vittime di tratta — aggiunge tra
  l'altro il rinvio all'art. 17 c. 2 d.lgs. 142). NON in vigore oggi → i siti
  restano corretti FINO al 15/7/2026 compreso; snapshot delle versioni future in
  `nm_fresh_20260710/*/future_*.html`. AZIONE FUTURA: ricoordinare dopo il 16/7.
- Artt. 35-bis.1/.2/.3 d.lgs. 25 su Normattiva = lapidi «NON PIÙ PREVISTO»
  (d.l. 145/2024, eliminati in conversione) — mai in vigore, correttamente
  assenti dal sito.

## Decisioni (classe → azione)

| # | Atto | Punto | Classe | Decisione |
|---|------|-------|--------|-----------|
| 1 | 25 | art. 26 c. 3 (e c. 5) | BASE-PARSE (a-capo del giugno mangiava «3.» come falso marcatore) | ~~Swap del sorgente~~ REVERTITO: l'art. 26 c. 3 È novellato (lett. g) n. 4: reg. 604/2013 → Parte III reg. 2024/1351) e il fresh ha la novella già consolidata → il pair non matchava più. Fix vero: guardia `comma_marker` nel parser di TUTTI i builder (un «N.» a inizio riga NON è un nuovo comma se la riga precedente termina con «comma/articolo/lettera/…» troncato dall'a-capo) |
| 2 | 25 | art. 32 c. 1 | OUR-ERROR (punteggiatura) | La lettera b-quater) inserita deve essere preceduta da «;» non «.» (coordinazione Normattiva): correggere pair p.1 in amendments.json |
| 3 | 25 | art. 32 c. 4 | OUR-ERROR (virgola aggiunta) + resa Normattiva | Novella letterale: «b-bis) b-ter) e b-quater),» senza virgola dopo b-bis) → correggere pair p.2. Residuo «b-quater)» vs «b-quater» = Normattiva PERDE la parentesi nel marcatore ((…)) → whitelist `equivalente-verificato` (il sito segue la novella GU) |
| 4 | 25 | art. 35 c. 2-bis | placeholder-artifact | Nessuna azione (sito: periodo barrato; Normattiva: avviso «PERIODO SOPPRESSO») |
| 5 | 142 | art. 22 c. 1 | OUR-ERROR (virgola aggiunta) | La novella inserisce esattamente «, comma 4» senza virgola finale → correggere pair g1 |
| 6 | 286 | art. 10 c. 2-quater | INAPPLICATA DA NORMATTIVA | La sostituzione «ingresso»→«ingresso o reingresso» (art. 12 c. 2 lett. a) n. 4) NON è applicata da Normattiva (il vigente recava già «reingresso»: nulla da sostituire). Normattiva=verità → rimuovere l'inserzione «ingresso o» (voce a4 spostata in `_non_applicate` di amendments.json, motivazione inclusa). FLAG per il legale |
| 7 | 286 | art. 39-bis.1 | ARTICOLO MANCANTE DAL GIUGNO (bug fetch: articoli decimali invisibili alla vecchia scoperta URL) | In vigore dal 5/7/2018 («Permesso di soggiorno per ricerca lavoro o imprenditorialità degli studenti»), mai presente sul sito → aggiungere `nm_html_286/a_9_39_2_20.html` dal fresh + estendere `fkey()` dei builder a 4 interi per l'ordinamento (39-bis < 39-bis.1 < 39-ter) |
| 8 | 286 | art. 10 c. 1, art. 10-ter c. 1/1-bis, art. 12 c. 1/1-bis, art. 14 c. 5-quater | SEGMENTAZIONE COMMI (Normattiva spezza/fonde i commi a seconda degli a-capo della versione; testo IDENTICO) | Nessuna modifica al sito; comparatore esteso con fallback a livello di ARTICOLO (`ok-segmentazione-commi`). NB art. 12 c. 1-bis (aggravante sanzioni UE) è testo già presente nel sito dentro il c. 1 |
| 9 | 25 | rubriche con parentesi | RESA (le versioni riconsolidate racchiudono la rubrica in parentesi) | Comparatore: `canon_rubrica`. Builder 25: backport `_unwrap_outer_parens` (già nei builder 142/286/251) per coerenza di visualizzazione |

## Interventi che NON si fanno (e perché)

- **Nessuno swap dei sorgenti degli articoli NOVELLATI** (il modello
  tracked-changes richiede la base pre-d.l.; i fresh hanno già le modifiche
  consolidate: le pairs non matcherebbero più).
- **Niente recepimento d.lgs. 115/2026** oggi (non in vigore) — pianificato.
