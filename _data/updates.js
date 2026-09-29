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
 *
 * `en` e `fr` devono rispecchiare `it` voce per voce (stesse 5 voci, stesso ordine): vedi TRADUZIONI.md.
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
  },  en: {
    label: 'Latest updates',
    pauseLabel: 'Pause the updates',
    items: [
      {
        date: "22 September 2026",
        text: "Venice Court: where the application predates the Ministerial Decree on authorised places, the border procedure is unlawful",
        cta: "Read the summary",
        href: "/en/giurisprudenza/trib-venezia-13622-2026-09-22.html",
      },
      {
        date: "22 September 2026",
        text: "Varese Prefettura: in its services, the document issued at registration stands in for the asylum-seeker permit",
        cta: "Read the summary",
        href: "/en/circolari/prefettura-varese-93-2026-09-22.html",
      },
      {
        date: "21 September 2026",
        text: "Venice Court: special needs identified at screening must be reassessed by the Commissione before any border procedure",
        cta: "Read the summary",
        href: "/en/giurisprudenza/trib-venezia-13298-2026-09-21.html",
      },
      {
        date: "20 September 2026",
        text: "Bologna Court: the C3 is registration, not lodging; former procedural rules apply to applications made before 12 June",
        cta: "Read the summary",
        href: "/en/giurisprudenza/trib-bologna-13060-2026-09-20.html",
      },
      {
        date: "19 September 2026",
        text: "Milan Court: apprehension under Article 43(1)(b) requires a close temporal and spatial link with the crossing",
        cta: "Read the summary",
        href: "/en/giurisprudenza/trib-milano-36319-2026-09-19.html",
      },
    ],
  },
  fr: {
    label: 'Dernières mises à jour',
    pauseLabel: 'Mettre les mises à jour en pause',
    items: [
      {
        date: "22 septembre 2026",
        text: "Tribunal de Venise : si la demande précède le décret ministériel sur les lieux habilités, la procédure à la frontière est illégale",
        cta: "Lire la fiche",
        href: "/fr/giurisprudenza/trib-venezia-13622-2026-09-22.html",
      },
      {
        date: "22 septembre 2026",
        text: "Prefettura de Varèse : dans ses services, le document délivré à l'enregistrement tient lieu de titre de demandeur d'asile",
        cta: "Lire la fiche",
        href: "/fr/circolari/prefettura-varese-93-2026-09-22.html",
      },
      {
        date: "21 septembre 2026",
        text: "Tribunal de Venise : besoins particuliers relevés au filtrage, la Commissione doit les réévaluer avant la procédure à la frontière",
        cta: "Lire la fiche",
        href: "/fr/giurisprudenza/trib-venezia-13298-2026-09-21.html",
      },
      {
        date: "20 septembre 2026",
        text: "Tribunal de Bologne : le C3 vaut enregistrement et non introduction ; règles antérieures pour les demandes avant le 12 juin",
        cta: "Lire la fiche",
        href: "/fr/giurisprudenza/trib-bologna-13060-2026-09-20.html",
      },
      {
        date: "19 septembre 2026",
        text: "Tribunal de Milan : l'interpellation de l'art. 43, par. 1, point b), exige un lien temporel et spatial étroit avec le franchissement",
        cta: "Lire la fiche",
        href: "/fr/giurisprudenza/trib-milano-36319-2026-09-19.html",
      },
    ],
  },
};
