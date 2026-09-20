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
 * `text` ≤ 130 CARATTERI. Il nastro scorre a 60 px/s fissi e la finestra
 * visibile è ~890 px (1200 del container meno label, pulsante di pausa e le
 * sfumature laterali): a 130 char su Inter 14 px la voce intera
 * (`date + text + cta`) sfora leggermente la finestra, quindi durante lo
 * scorrimento non è mai tutta visibile insieme — scelta consapevole per
 * privilegiare un registro più esplicito rispetto alla sintesi da titolo.
 * Se si vuole di nuovo il "tutto in finestra", tornare a ≤ 95 (≤ 85 quando
 * `date` è una stringa lunga come «in G.U. il 10 agosto 2026»).
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
        date: '14 settembre 2026',
        text: 'Trib. Trieste: la soglia del 20% non dispensa la Commissione dalla valutazione individuale delle esigenze procedurali di genere',
        cta: 'Leggi la scheda',
        href: '/giurisprudenza/trib-trieste-vulnerabilita-2026-09-14.html',
      },
      {
        date: '12 settembre 2026',
        text: "Trib. Roma: l'esame accelerato presuppone le garanzie del Capo II, senza informativa e orientamento legale è procedura ordinaria",
        cta: 'Leggi la scheda',
        href: '/giurisprudenza/trib-roma-39909-2026-09-12.html',
      },
      {
        date: '11 settembre 2026',
        text: 'Trib. Milano: disapplica la designazione del Bangladesh come paese sicuro, la scheda ministeriale esclude le persone LGBTQI+',
        cta: 'Leggi la scheda',
        href: '/giurisprudenza/trib-milano-26906-2026-09-11.html',
      },
      {
        date: '11 settembre 2026',
        text: 'Trib. Bologna: sospensione automatica se la determina di procedura del Presidente della Commissione territoriale non è firmata',
        cta: 'Leggi la scheda',
        href: '/giurisprudenza/trib-bologna-17417-2026-09-11.html',
      },
      {
        date: '10 settembre 2026',
        text: 'Trib. Bologna: le esigenze procedurali particolari escludono la procedura di frontiera, non le nega un operatore allo screening',
        cta: 'Leggi la scheda',
        href: '/giurisprudenza/trib-bologna-13748-2026-09-10.html',
      },
    ],
  },
};
