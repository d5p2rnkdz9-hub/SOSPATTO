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
 * REGOLA: massimo 5 voci, in ordine di data del provvedimento decrescente, con
 * una sola voce per filone (se due decisioni gemelle dicono la stessa cosa, ne
 * entra una). Aggiungendo una novità si toglie la voce in fondo.
 *
 * `text` ≤ 95 CARATTERI — e ≤ 85 se `date` è una stringa lunga come
 * «in G.U. il 10 agosto 2026». Non è un vezzo tipografico: il nastro scorre a
 * 60 px/s fissi, quindi la lunghezza è tempo, e la finestra visibile è ~890 px
 * (1200 del container meno label, pulsante di pausa e le sfumature laterali).
 * Quel che deve entrare negli 890 px è la voce INTERA, cioè
 * `date + text + cta`: se sfonda, non si vede mai per intero e va inseguita
 * mentre esce da sinistra. Misurato su Inter 14 px, le 5 voci attuali stanno fra
 * 773 e 863 px e il ciclo completo dura ~68 s; con le voci lunghe di prima ne
 * bastavano 4 per arrivare a 82 s, nessuna delle quali entrava nella finestra.
 *
 * REGISTRO: un titolo di giornale, non una massima in miniatura. Principio più
 * l'inciso che chiude il senso; il resto lo legge chi clicca. Il soggetto è la
 * corte («Trib. Bologna: …»), l'esito processuale entra solo se serve a capire.
 */
module.exports = {
  it: {
    label: 'Ultimi aggiornamenti',
    pauseLabel: 'Metti in pausa gli aggiornamenti',
    items: [
      {
        date: '4 settembre 2026',
        text: 'Trib. Bologna: il C3 tardivo per colpa dell\'Amministrazione non sposta la domanda al Patto',
        cta: 'Leggi la scheda',
        href: '/giurisprudenza/trib-bologna-13590-2026-09-04.html',
      },
      {
        date: '20 agosto 2026',
        text: 'Trib. Trieste: il D.M. zone di frontiera non sana le procedure avviate prima della G.U.',
        cta: 'Leggi la scheda',
        href: '/giurisprudenza/trib-trieste-4748-2026-08-20.html',
      },
      {
        date: '19 agosto 2026',
        text: 'Trib. Roma: sospeso un trasferimento Dublino, il decreto cita un articolo che non indica',
        cta: 'Leggi la scheda',
        href: '/giurisprudenza/trib-roma-2026-08-19.html',
      },
      {
        date: '17 agosto 2026',
        text: 'Trib. Perugia: la Commissione applica le norme vecchie, il ricorso le segue ed è tempestivo',
        cta: 'Leggi la scheda',
        href: '/giurisprudenza/trib-perugia-3003-2026-08-17.html',
      },
      // Datato 21 luglio ma in nastro con la data di pubblicazione in G.U. (10 agosto):
      // per il lettore è quella la data che conta.
      {
        date: 'in G.U. il 10 agosto 2026',
        text: 'Nuovo D.M. zone di frontiera: valichi Schengen e porti, 19 nuove sezioni di Commissione',
        cta: 'Leggi la scheda',
        href: '/circolari/dm-zone-frontiera-2026-07-21.html',
      },
    ],
  },
};
