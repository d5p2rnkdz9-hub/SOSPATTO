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
        date: '1° ottobre 2026',
        text: "Trib. Torino: la soglia del 20% non esclude l'autorizzazione a permanere, violenza indiscriminata nel Khyber Pakhtunkhwa",
        cta: 'Leggi la scheda',
        href: '/giurisprudenza/trib-torino-18229-2026-10-01.html',
      },
      {
        date: '1° ottobre 2026',
        text: 'Trib. Bologna: procedura di frontiera avviata sul solo dato Eurostat del 20%, non è instaurata e il ricorso sospende ex lege',
        cta: 'Leggi la scheda',
        href: '/giurisprudenza/trib-bologna-15588-2026-10-01.html',
      },
      {
        date: '30 settembre 2026',
        text: 'Trib. Venezia: la vulnerabilità sopravvenuta impone la revisione delle garanzie, esclusa la procedura di frontiera accelerata',
        cta: 'Leggi la scheda',
        href: '/giurisprudenza/trib-venezia-13922-2026-09-30.html',
      },
      {
        date: '29 settembre 2026',
        text: 'Trib. Milano: il ritardo della Questura nella formalizzazione non ricade sul richiedente, vale la disciplina alla manifestazione',
        cta: 'Leggi la scheda',
        href: '/giurisprudenza/trib-milano-31896-2026-09-29.html',
      },
      {
        date: "in G.U. il 29 settembre 2026",
        text: "Nuovo D.L. 168/2026: regime transitorio prorogato al 30 aprile 2027, il documento rilasciato alla registrazione vale un anno",
        cta: "Leggi il testo",
        href: "/patto-interattivo/dl-168-2026/index.html",
      },
    ],
  },  en: {
    label: 'Latest updates',
    pauseLabel: 'Pause the updates',
    items: [
      {
        date: "1 October 2026",
        text: "Turin Court: the 20% threshold does not bar authorisation to remain, generalised violence in Khyber Pakhtunkhwa",
        cta: "Read the summary",
        href: "/en/giurisprudenza/trib-torino-18229-2026-10-01.html",
      },
      {
        date: "1 October 2026",
        text: "Bologna Court: a border procedure started on the Eurostat 20% figure alone is not validly initiated, the appeal is suspensive",
        cta: "Read the summary",
        href: "/en/giurisprudenza/trib-bologna-15588-2026-10-01.html",
      },
      {
        date: "30 September 2026",
        text: "Venice Court: supervening vulnerability requires review of procedural guarantees, accelerated border procedure excluded",
        cta: "Read the summary",
        href: "/en/giurisprudenza/trib-venezia-13922-2026-09-30.html",
      },
      {
        date: "29 September 2026",
        text: "Milan Court: delay by the Questura in formalising the application does not fall on the applicant, the law at the wish applies",
        cta: "Read the summary",
        href: "/en/giurisprudenza/trib-milano-31896-2026-09-29.html",
      },
      {
        date: "in the Official Gazette on 29 September 2026",
        text: "New Decree-Law 168/2026: transitional regime extended to 30 April 2027, the document issued on registration is valid for one year",
        cta: "Read the text",
        href: "/patto-interattivo/dl-168-2026/index.html",
      },
    ],
  },
  fr: {
    label: 'Dernières mises à jour',
    pauseLabel: 'Mettre les mises à jour en pause',
    items: [
      {
        date: "1er octobre 2026",
        text: "Tribunal de Turin : le seuil de 20 % n'empêche pas l'autorisation de rester, violence généralisée dans le Khyber Pakhtunkhwa",
        cta: "Lire la fiche",
        href: "/fr/giurisprudenza/trib-torino-18229-2026-10-01.html",
      },
      {
        date: "1er octobre 2026",
        text: "Tribunal de Bologne : procédure à la frontière engagée sur la seule donnée Eurostat de 20 %, non valable, recours suspensif",
        cta: "Lire la fiche",
        href: "/fr/giurisprudenza/trib-bologna-15588-2026-10-01.html",
      },
      {
        date: "30 septembre 2026",
        text: "Trib. Venise : la vulnérabilité survenue en cours de procédure impose la révision des garanties, procédure à la frontière exclue",
        cta: "Lire la fiche",
        href: "/fr/giurisprudenza/trib-venezia-13922-2026-09-30.html",
      },
      {
        date: "29 septembre 2026",
        text: "Tribunal de Milan : le retard de la Questura ne pèse pas sur le demandeur, la règle au moment de la manifestation s'applique",
        cta: "Lire la fiche",
        href: "/fr/giurisprudenza/trib-milano-31896-2026-09-29.html",
      },
      {
        date: "au J.O. le 29 septembre 2026",
        text: "Nouveau décret-loi 168/2026 : régime transitoire prorogé au 30 avril 2027, le document délivré à l'enregistrement vaut un an",
        cta: "Lire le texte",
        href: "/patto-interattivo/dl-168-2026/index.html",
      },
    ],
  },
};
