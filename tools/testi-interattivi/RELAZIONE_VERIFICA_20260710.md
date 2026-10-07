# Relazione di verifica — testi interattivi coordinati col d.l. 100/2026
**Data verifica: 10 luglio 2026 — Fonte di verità: Normattiva (testo vigente al 10/7/2026)**

## 1. Sintesi

| Atto | Testo vs Normattiva | Rinvii | Esito |
|------|--------------------|--------|-------|
| d.lgs. 25/2008 (procedure) | ✅ conforme (2 equivalenze documentate) | ✅ 363 link, 0 problemi, 0 mislink | 🟢 |
| d.lgs. 142/2015 (accoglienza) | ✅ conforme | ✅ 540 link, 0 problemi, 0 mislink | 🟢 |
| d.lgs. 286/1998 (T.U. immigrazione) | ✅ conforme (4 equivalenze di segmentazione) | ✅ 1.014 link, 0 problemi, 0 mislink | 🟢 |
| d.lgs. 251/2007 (qualifiche) | ✅ conforme al 100% | ✅ 99 link, 0 problemi, 0 mislink | 🟢 |

Il testo FINALE di ciascun sito (base + modifiche evidenziate) coincide oggi col
vigente Normattiva, articolo per articolo e comma per comma. Durante la verifica
sono stati trovati e **corretti** 5 scostamenti testuali minori e **13 rinvii
mal collegati**; è stato **aggiunto un articolo intero** che mancava (art.
39-bis.1 T.U.). Tutto il dettaglio ai §§ 3–4.

## 2. Stato normativo (novità rilevanti scoperte)

1. **D.l. 100/2026 NON ancora convertito** (verificato su Normattiva: nessuna
   legge di conversione al 10/7). I banner «in corso di conversione» dei siti
   restano corretti. Gli artt. 10/11/12 vigenti coincidono con la GU originaria.
   **Scadenza conversione: ~11 agosto 2026** → alla conversione andrà rifatta
   questa verifica (basta rilanciare la pipeline, § 6).
2. **⚠️ NOVITÀ: d.lgs. 12 giugno 2026, n. 115** (GU 1/7/2026 n. 150, **in
   vigore dal 16 luglio 2026** — materia vittime di tratta). Modifica, tra
   l'altro: **art. 32, c. 3-bis d.lgs. 25** (aggiunge «In tal caso si applica
   l'articolo 17, comma 2, del d.lgs. 142/2015»), **art. 17 d.lgs. 142** e
   **art. 18 d.lgs. 286**. NON è in vigore oggi: i siti sono corretti fino al
   15/7 compreso. Le versioni future sono già scaricate
   (`nm_fresh_20260710/*/future_*.html`). **AZIONE: dopo il 16/7 recepire le
   tre modifiche** (o rilanciare la pipeline).
3. Artt. 35-bis.1/.2/.3 d.lgs. 25 esistono su Normattiva solo come lapidi
   «ARTICOLO NON PIÙ PREVISTO» (d.l. 145/2024, soppressi in conversione): mai
   in vigore, correttamente assenti dai siti.

## 3. Conformità testuale — discrepanze trovate e risolte

Metodo: doppio confronto per ogni atto — (A) snapshot di giugno vs Normattiva
odierna (isola ciò che è cambiato); (B) **testo finale del sito vs Normattiva
odierna** (la verifica di verità). Statistiche finali: 25 → 203 commi identici;
142 → 192; 286 → 695+; 251 → tutti. Findings aperti: **0**.

### Correzioni applicate (Normattiva = verità)

1. **[25, art. 32 c. 1]** La lettera b-quater) inserita era preceduta da «.» —
   il coordinamento ufficiale usa «**;**» → corretta la pair in amendments.json.
2. **[25, art. 32 c. 4]** Avevamo aggiunto una virgola dopo «b-bis)» che la
   novella non prevede → allineato al testo letterale della novella
   («lettere b), b-bis) b-ter) e b-quater),»).
3. **[142, art. 22 c. 1]** La novella inserisce esattamente «, comma 4» —
   avevamo aggiunto una virgola dopo «4» → rimossa.
4. **[25, art. 26 c. 3]** Il parser di giugno perdeva «3.» nel rinvio
   «dall'articolo 3, comma 3» (l'a-capo di Normattiva metteva «3.» a inizio
   riga, scambiato per un marcatore di comma) → guardia `comma_marker` nel
   parser di TUTTI i builder; il testo ora è integro.
5. **[286, art. 39-bis.1]** ⚠️ **Articolo intero assente dal sito** («Permesso
   di soggiorno per ricerca lavoro o imprenditorialità degli studenti», in
   vigore dal 2018): il fetch di giugno non "vedeva" gli articoli decimali
   (parametro `idSottoArticolo1` di Normattiva). Aggiunto il sorgente; il TU
   ora ha 79 articoli, in ordine corretto (39-bis → 39-bis.1 → 39-ter).

### 🔶 Flag interpretativo per il legale

**[286, art. 10 c. 2-quater] — novella «ingresso»→«ingresso o reingresso» NON
applicata da Normattiva.** L'art. 12, c. 2, lett. a) n. 4 d.l. 100/2026 ordina
la sostituzione, ma il testo vigente recava già «reingresso» e la parola
«ingresso» da sola non esiste nel comma: il coordinamento ufficiale ha lasciato
il testo INVARIATO. A giugno l'avevamo resa come inserimento di «ingresso o»
(flag già segnalato allora). In ossequio alla regola «Normattiva è la verità»
l'inserzione è stata **rimossa dal sito**; la voce resta documentata in
`286-98-interattivo/amendments.json` → `_non_applicate` con motivazione. Se in
sede di conversione il testo verrà "sanato", la voce si ripristina.

### Equivalenze documentate (nessuna azione, testo normativo identico)

- **[25, art. 32 c. 4]** Normattiva perde la parentesi di «b-quater)» nella
  resa del marcatore ((…)) — il sito segue la novella GU (whitelist).
- **[25, art. 35 c. 2-bis]** Il sito rende il periodo soppresso come testo
  barrato; Normattiva mostra l'avviso «PERIODO SOPPRESSO DAL D.L. …».
- **[286, artt. 10, 10-ter, 12, 14]** Normattiva spezza/fonde alcuni commi
  decimali (1.1, 1-bis, 5-quater.1) secondo gli a-capo della versione servita;
  il testo integrale coincide (verificato a livello di articolo).

## 4. Verifica dei rinvii (~2.000 collegamenti)

1. **Coerenza deterministica** (verificatori indipendenti): ogni link punta a
   un bersaglio esistente, nessun tooltip vuoto, href ben formati →
   **0 problemi in tutti e quattro i siti**.
2. **Scan semantico dei mislink** (nuovo `scan_mislink_semantico.py`, con
   vocabolario esteso ai «testo unico …»): trovati e **corretti 13 rinvii
   REALI mal collegati** che puntavano all'atto ospite invece che all'atto
   citato. Due cause radice, sistemate nella grammatica di TUTTI i builder:
   - **Bug di precedenza regex** nel qualificatore «lettera c-quater)» (veniva
     consumata solo la «c», il rinvio ricadeva sull'atto ospite). Colpiva ad
     es. «art. 11 … del d.P.R. 394/1999» in T.U. art. 6 e l'anafora «della
     medesima legge» (l. 468/1978) in 251 art. 33.
   - **Citazioni «del testo unico delle disposizioni …, di cui al …»** (con
     descrittore lungo, anche preceduto da «citato»): il tail non veniva visto.
     Ora «art. 19/30/6/5 del testo unico … immigrazione» nel d.lgs. 251
     **deep-linkano al sito del T.U. 286**; le citazioni del d.P.R. 445/2000
     (documentazione amministrativa) in 142/286 → link Normattiva corretto.
   Dopo le correzioni: **0 mislink su tutti e quattro i siti**.
3. **Sospetti da revisione giurista**: nessun sospetto NUOVO rispetto ai 38
   già confermati a giugno; i 3 sospetti del 251 si sono **risolti da soli**
   (erano sintomi dei mislink di cui sopra). Nulla da rivedere.

## 5. Azioni residue (calendario)

| Quando | Azione |
|--------|--------|
| **dal 16/7/2026** | Recepire d.lgs. 115/2026 (art. 32 c. 3-bis d.lgs. 25; art. 17 d.lgs. 142; art. 18 d.lgs. 286) — versioni future già scaricate |
| **alla conversione del d.l. 100** (entro ~11/8/2026) | Ri-verificare i tre testi coordinati contro il testo convertito; aggiornare banner/disclaimer («convertito con L. …») |
| quando deciso | Pubblicazione: il bundle aggiornato è pronto in `~/Downloads/patto-interattivo` (+ .zip); il push su GitHub/Netlify NON è stato fatto (come concordato) |

## 6. Metodo e strumenti (riusabili)

- `fetch_normattiva.py` — fetcher parametrizzato (handshake cookie, modalità
  classica, scoperta articoli dalla pagina fresca, **articoli decimali**,
  **versioni a decorrenza futura** salvate a parte, manifest sha256).
- `confronto_normattiva.py` — comparatore a tre modelli (base / sito-finale /
  fresh) con normalizzazione condivisa, regole di equivalenza (abrogazioni,
  placeholder, segmentazione commi) e whitelist auditabile
  (`confronto_whitelist.json`). Report in `nm_fresh_20260710/reports/`.
- `scan_mislink_semantico.py` — scan dei mislink self→atto-esterno.
- Triage completo delle decisioni: `nm_fresh_20260710/triage.md`.
- Limiti: fanno fede la GU e Normattiva; le versioni «future» non sono state
  incorporate (per scelta: il sito mostra il vigente); i marcatori ((…)) e la
  tipografia di Normattiva sono normalizzati simmetricamente nel confronto.

Bundle finale verificato: 199 file — siti ricompilati 2-pass, verificatori
tutti a zero, copia off-iCloud in `~/Downloads/patto-interattivo`.
