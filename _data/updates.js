/**
 * ULTIMI AGGIORNAMENTI — nastro scorrevole sotto il menu.
 *
 * Stessa forma di nav.js: una chiave per lingua (per ora solo `it`) con
 * `label` + `items`. `items` in ordine dal più recente al più vecchio: tutti
 * scorrono in un nastro continuo, aggiungerne uno allunga il nastro senza
 * accelerare lo scorrimento (velocità fissa ~60 px/s, in updates-banner.liquid).
 *
 * Campi di un item:
 *   date      → data già formattata
 *   text      → la novità, in una riga
 *   cta       → etichetta del link
 *   href      → destinazione (interna: passa da `| url`; esterna: usa external)
 *   external  → apre in una nuova scheda (per link fuori dal sito)
 *
 * REGOLA: massimo 4 voci, in ordine di data del provvedimento decrescente, con
 * una sola voce per filone (se due decisioni gemelle dicono la stessa cosa, ne
 * entra una). Aggiungendo una novità si toglie la voce in fondo.
 */
module.exports = {
  it: {
    label: 'Ultimi aggiornamenti',
    pauseLabel: 'Metti in pausa gli aggiornamenti',
    items: [
      {
        date: '27 luglio 2026',
        text: 'Trib. Caltanissetta: autorizzato a permanere per compressione del diritto di difesa in frontiera',
        cta: 'Leggi la scheda',
        href: '/giurisprudenza/trib-caltanissetta-1137-2026-07-27.html',
      },
      {
        date: '25 luglio 2026',
        text: 'Trib. Palermo: non basta un modulo con QR code a informare chi è in procedura di frontiera',
        cta: 'Leggi la scheda',
        href: '/giurisprudenza/trib-palermo-8695-2026-07-25.html',
      },
      {
        date: '25 luglio 2026',
        text: 'Trib. Palermo: il tasso Eurostat ≤ 20% è solo indiziario, non basta per la procedura di frontiera',
        cta: 'Leggi la scheda',
        href: '/giurisprudenza/trib-palermo-9739-2026-07-25.html',
      },
      {
        date: '20 luglio 2026',
        text: 'T.A.R. Lombardia: istruttoria sulla class action ASGI-NAGA per i ritardi nell’accesso alla procedura d’asilo a Milano',
        cta: 'Leggi la scheda',
        href: '/giurisprudenza/tar-lombardia-3818-2026-07-20.html',
      },
    ],
  },
};
