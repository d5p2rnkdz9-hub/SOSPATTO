// Catalogo dei testi consultabili nel lettore interattivo (/patto-interattivo/).
// I 10 atti UE stanno a /patto-interattivo/<num>.html, le norme italiane a
// /patto-interattivo/<slug>/index.html (stessa struttura del bundle su
// sospermesso.it e studiolegaleoltre.org — vedi sites.json nel progetto sorgente).
module.exports = {
  // data dell'ultima verifica dei testi (EUR-Lex / Normattiva)
  aggiornamento: '10 luglio 2026',

  ue: [
    {
      num: '1346',
      tipo: 'Direttiva',
      numero: 'UE 2024/1346',
      titolo: 'Direttiva accoglienza',
      desc: "Norme sull'accoglienza dei richiedenti protezione internazionale.",
      icon: '🏠',
    },
    {
      num: '1347',
      tipo: 'Regolamento',
      numero: 'UE 2024/1347',
      titolo: 'Regolamento qualifiche',
      desc: 'Criteri per il riconoscimento dello status di rifugiato e della protezione sussidiaria.',
      icon: '✅',
    },
    {
      num: '1348',
      tipo: 'Regolamento',
      numero: 'UE 2024/1348',
      titolo: 'Regolamento procedure',
      desc: 'Procedura comune europea per la protezione internazionale.',
      icon: '📋',
    },
    {
      num: '1349',
      tipo: 'Regolamento',
      numero: 'UE 2024/1349',
      titolo: 'Regolamento rimpatrio alla frontiera',
      desc: 'Procedure di rimpatrio applicabili alla frontiera.',
      icon: '↩️',
    },
    {
      num: '1350',
      tipo: 'Regolamento',
      numero: 'UE 2024/1350',
      titolo: 'Regolamento reinsediamento',
      desc: "Quadro dell'Unione per il reinsediamento e l'ammissione umanitaria.",
      icon: '🤝',
    },
    {
      num: '1351',
      tipo: 'Regolamento',
      numero: 'UE 2024/1351',
      titolo: 'Regolamento RAMM (Dublino)',
      desc: "Gestione dell'asilo e della migrazione: sostituisce il sistema di Dublino.",
      icon: '🗂️',
    },
    {
      num: '1352',
      tipo: 'Regolamento',
      numero: 'UE 2024/1352',
      titolo: 'Modifiche ECRIS-TCN',
      desc: 'Modifiche al sistema europeo di informazione sui casellari giudiziari di cittadini di paesi terzi.',
      icon: '🗄️',
    },
    {
      num: '1356',
      tipo: 'Regolamento',
      numero: 'UE 2024/1356',
      titolo: 'Regolamento screening',
      desc: 'Accertamenti su cittadini di paesi terzi alle frontiere esterne.',
      icon: '🔍',
    },
    {
      num: '1358',
      tipo: 'Regolamento',
      numero: 'UE 2024/1358',
      titolo: 'Regolamento Eurodac',
      desc: 'Banca dati europea delle impronte digitali e dei dati biometrici.',
      icon: '🫆',
    },
    {
      num: '1359',
      tipo: 'Regolamento',
      numero: 'UE 2024/1359',
      titolo: 'Regolamento crisi e forza maggiore',
      desc: 'Situazioni di crisi, strumentalizzazione e forza maggiore in materia di migrazione e asilo.',
      icon: '🚨',
    },
  ],

  it: [
    {
      slug: 'dlgs-25-2008',
      titolo: 'D.Lgs. 25/2008',
      sotto: 'Procedure per il riconoscimento della protezione internazionale',
      coord: 'Testo coordinato con il d.l. 100/2026 (art. 11) — modifiche evidenziate',
      icon: '⚖️',
    },
    {
      slug: 'dlgs-142-2015',
      titolo: 'D.Lgs. 142/2015',
      sotto: 'Accoglienza dei richiedenti protezione internazionale',
      coord: 'Testo coordinato con il d.l. 100/2026 (art. 10) — modifiche evidenziate',
      icon: '🏘️',
    },
    {
      slug: 'dlgs-286-1998',
      titolo: 'D.Lgs. 286/1998',
      sotto: "Testo unico dell'immigrazione",
      coord: 'Testo coordinato con il d.l. 100/2026 (art. 12) — modifiche evidenziate',
      icon: '📕',
    },
    {
      slug: 'dlgs-251-2007',
      titolo: 'D.Lgs. 251/2007',
      sotto: 'Qualifiche: status di rifugiato e protezione sussidiaria',
      coord: 'Testo vigente con rinvii navigabili',
      icon: '📗',
    },
  ],
};
