# Piano di promozione — Ciclo di incontri sulla mitologia

Piano di marketing **interattivo** per promuovere un ciclo di incontri sulla
mitologia in chiave psicologica, rivolto a psicoterapeuti e psicologi ma aperto
a un pubblico colto più ampio.

È una singola pagina HTML **self-contained** (nessuna dipendenza esterna,
nessuna connessione richiesta): funziona interamente in locale e salva i
progressi (checklist, impostazioni) nel browser.

## Come si avvia

Dalla cartella `piano-marketing-mitologia/`:

```bash
./serve.sh          # poi apri http://localhost:8080
```

oppure, a mano:

```bash
python3 -m http.server 8080
# → http://localhost:8080
```

In alternativa puoi anche solo **aprire `index.html` con un doppio clic**:
tutto funziona anche da file locale.

## Cosa contiene

- **Setup rapido** — personalizzi nome del ciclo, formato (online/presenza),
  città, data, prezzo e obiettivo iscritti: il piano si adatta (scadenze,
  obiettivi, testi pronti).
- **Strategia in sintesi** e definizione dei pubblici.
- **Analisi della concorrenza** (offerte comparabili in Italia + riferimenti
  internazionali, con fonti).
- **Canali di promozione** con matrice sforzo/impatto interattiva e mix
  consigliato per 3 scenari di budget.
- **Piano operativo a 8 settimane** con checklist spuntabili (i progressi
  restano salvati nel browser).
- **Kit di contenuti**: testi pronti da copiare (Instagram, email, gruppi
  Facebook, WhatsApp, newsletter partner, pagina evento).
- **KPI e funnel** con obiettivi calcolati a ritroso dall'obiettivo iscritti.
- **Errori da evitare** e **fonti** della ricerca.

## Note

- I progressi si salvano in `localStorage` del browser (nessun dato esce dal
  computer). Il pulsante «Azzera» nella pagina li cancella.
- I numeri di benchmark sono stime di settore, citate nelle fonti: vanno letti
  come ordini di grandezza, non promesse.
- La pagina è stampabile (Ctrl/Cmd+P): esce un documento pulito da condividere.
