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
        date: '22 settembre 2026',
        text: "Trib. Venezia: se la domanda precede l'entrata in vigore del D.M. sui luoghi abilitati, la procedura di frontiera è illegittima",
        cta: 'Leggi la scheda',
        href: '/giurisprudenza/trib-venezia-13622-2026-09-22.html',
      },
      {
        date: '22 settembre 2026',
        text: 'Prefettura di Varese: nei servizi il documento rilasciato alla registrazione tiene luogo del permesso per richiesta asilo',
        cta: 'Leggi la scheda',
        href: '/circolari/prefettura-varese-93-2026-09-22.html',
      },
      {
        date: '21 settembre 2026',
        text: 'Trib. Venezia: esigenze particolari rilevate allo screening, la Commissione deve rivalutarle prima della procedura di frontiera',
        cta: 'Leggi la scheda',
        href: '/giurisprudenza/trib-venezia-13298-2026-09-21.html',
      },
      {
        date: '20 settembre 2026',
        text: 'Trib. Bologna: il C3 è registrazione e non formalizzazione, per le domande presentate prima del 12 giugno vale il rito previgente',
        cta: 'Leggi la scheda',
        href: '/giurisprudenza/trib-bologna-13060-2026-09-20.html',
      },
      {
        date: '19 settembre 2026',
        text: "Trib. Milano: il rintraccio dell'art. 43, par. 1, lett. b), esige uno stretto legame temporale e spaziale con l'attraversamento",
        cta: 'Leggi la scheda',
        href: '/giurisprudenza/trib-milano-36319-2026-09-19.html',
      },
    ],
  },
};
