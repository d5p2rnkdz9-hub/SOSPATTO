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
      // In testa pur essendo datato 21 luglio: per il lettore la data che conta è la
      // pubblicazione in G.U. (10 agosto), che lo rende il piu' recente del nastro.
      {
        date: 'in G.U. il 10 agosto 2026',
        text: 'NUOVO D.M. zone di frontiera: ai luoghi del d.m. 2019 si aggiungono i valichi Schengen e i porti, con 19 nuove sezioni delle Commissioni territoriali',
        cta: 'Leggi la scheda',
        href: '/circolari/dm-zone-frontiera-2026-07-21.html',
      },
      {
        date: '7 agosto 2026',
        text: 'Trib. Trieste: il d.m. 2019 sulle zone di frontiera è obsoleto, la procedura di frontiera non è applicabile a Gorizia',
        cta: 'Leggi la scheda',
        href: '/giurisprudenza/trib-trieste-4412-2026-08-07.html',
      },
      {
        date: '4 agosto 2026',
        text: 'Cassazione civile: anche post-Patto il richiedente è inespellibile fino alla scadenza del termine per impugnare',
        cta: 'Leggi la scheda',
        href: '/giurisprudenza/cass-24430-2026-08-04.html',
      },
      {
        date: '4 agosto 2026',
        text: 'Trib. Napoli: se la volontà è stata manifestata prima del 12 giugno, il Patto non si applica anche se il C3 è successivo',
        cta: 'Leggi la scheda',
        href: '/giurisprudenza/trib-napoli-17179-2026-08-04.html',
      },
    ],
  },
};
