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
 * Per aggiungere una novità: nuovo item in cima all'array `it.items`.
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
        text: 'Trib. Palermo: revocata l’autorizzazione a risiedere in frontiera (art. 5-quinquies)',
        cta: 'Leggi la scheda',
        href: '/giurisprudenza/trib-palermo-8694-2026-07-25.html',
      },
      {
        date: '25 luglio 2026',
        text: 'Trib. Palermo: il tasso Eurostat ≤ 20% è solo indiziario, non basta per la procedura di frontiera',
        cta: 'Leggi la scheda',
        href: '/giurisprudenza/trib-palermo-9739-2026-07-25.html',
      },
      {
        date: '23 luglio 2026',
        text: 'Trib. Bologna: decide nel merito il reclamo sull’autorizzazione a risiedere in luogo specifico',
        cta: 'Leggi la scheda',
        href: '/giurisprudenza/trib-bologna-10979-2026-07-23.html',
      },
      {
        date: '22 luglio 2026',
        text: 'Trib. Messina: il Patto non si applica a chi ha manifestato la volontà prima del 12 giugno 2026',
        cta: 'Leggi la scheda',
        href: '/giurisprudenza/trib-messina-2614-2026-07-22.html',
      },
    ],
  },
};
