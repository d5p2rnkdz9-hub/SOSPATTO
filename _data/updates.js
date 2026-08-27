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
        date: '20 agosto 2026',
        text: 'Trib. Trieste: il D.M. sulle zone di frontiera doveva esistere quando la procedura è stata avviata — la pubblicazione in G.U. del 10 agosto non sana le procedure anteriori',
        cta: 'Leggi la scheda',
        href: '/giurisprudenza/trib-trieste-4748-2026-08-20.html',
      },
      {
        date: '19 agosto 2026',
        text: 'Trib. Roma: sospeso un trasferimento Dublino perché il decreto dell\'Unità Dublino cita un articolo del Regolamento rimasto non indicato',
        cta: 'Leggi la scheda',
        href: '/giurisprudenza/trib-roma-2026-08-19.html',
      },
      {
        date: '17 agosto 2026',
        text: 'Trib. Perugia: se la Commissione decide una domanda post-Patto con le norme previgenti, anche il ricorso si esamina con quelle — ed è tempestivo',
        cta: 'Leggi la scheda',
        href: '/giurisprudenza/trib-perugia-3003-2026-08-17.html',
      },
      // Datato 21 luglio ma in nastro con la data di pubblicazione in G.U. (10 agosto):
      // per il lettore è quella la data che conta.
      {
        date: 'in G.U. il 10 agosto 2026',
        text: 'NUOVO D.M. zone di frontiera: ai luoghi del d.m. 2019 si aggiungono i valichi Schengen e i porti, con 19 nuove sezioni delle Commissioni territoriali',
        cta: 'Leggi la scheda',
        href: '/circolari/dm-zone-frontiera-2026-07-21.html',
      },
    ],
  },
};
