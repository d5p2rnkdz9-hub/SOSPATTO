// Vocabolario controllato dei macro-temi per giurisprudenza, circolari e dottrina.
// Ogni scheda usa in `temi:` SOLO le label qui elencate (verifica: npm run temi-check).
// `aliases` tiene traccia dei vecchi tag assorbiti, per riferimento e per il check.
module.exports = [
  {
    slug: 'accesso-alla-procedura',
    label: 'Accesso alla procedura',
    aliases: ['manifestazione di volontà', 'registrazione', 'formalizzazione',
      'attestazione di manifestazione', 'fotosegnalamento', 'appuntamenti', 'termini',
      'ritardo nella manifestazione', 'Questura', 'accesso ai diritti'],
  },
  {
    slug: 'screening',
    label: 'Screening',
    aliases: ['controlli di salute', 'sbarco', 'arrivi'],
  },
  {
    slug: 'procedura-di-frontiera',
    label: 'Procedura di frontiera',
    aliases: ['zone di frontiera', 'hotspot', 'frontiera'],
  },
  {
    slug: 'procedure-accelerate',
    label: 'Procedure accelerate',
    aliases: ['procedura accelerata'],
  },
  {
    slug: 'manifesta-infondatezza',
    label: 'Manifesta infondatezza',
    aliases: [],
  },
  {
    slug: 'paesi-sicuri-soglia-20',
    label: 'Paesi sicuri e soglia del 20%',
    aliases: ['paesi di origine sicuri', 'paesi con riconoscimento ≤ 20%',
      'tasso di riconoscimento', 'paesi di origine', 'categorie di persone'],
  },
  {
    slug: 'trattenimento',
    label: 'Trattenimento',
    aliases: ['trattenimento de facto', 'libertà personale'],
  },
  {
    slug: 'obbligo-di-soggiorno',
    label: 'Obbligo di soggiorno',
    aliases: [],
  },
  {
    slug: 'domanda-reiterata',
    label: 'Domanda reiterata',
    aliases: ['inammissibilità'],
  },
  {
    slug: 'garanzie-procedurali',
    label: 'Garanzie procedurali',
    aliases: ['colloquio', 'videoregistrazione', 'orientamento legale',
      'obblighi informativi', 'diritto di difesa', 'credibilità', 'onere della prova'],
  },
  {
    slug: 'rimedi-giurisdizionali',
    label: 'Rimedi giurisdizionali',
    aliases: ['autorizzazione a rimanere', 'sospensiva', 'sospensione automatica',
      'class action', 'processo', 'iscrizione a ruolo', 'ufficio per il processo'],
  },
  {
    slug: 'vulnerabilita',
    label: 'Vulnerabilità',
    aliases: ['tratta', 'categorie fragili', 'esigenze di accoglienza particolari'],
  },
  {
    slug: 'accoglienza',
    label: 'Accoglienza',
    aliases: ['CAS', 'termine di 90 giorni'],
  },
  {
    slug: 'regime-transitorio',
    label: 'Regime transitorio',
    aliases: ['disciplina transitoria', 'disciplina applicabile nel tempo', 'raccordo operativo'],
  },
  {
    slug: 'rimpatri',
    label: 'Rimpatri',
    aliases: ['regolamento rimpatri', 'ordine di rimpatrio', 'espulsione', 'allontanamento'],
  },
  {
    slug: 'esternalizzazione',
    label: 'Esternalizzazione',
    aliases: ['Protocollo Italia-Albania', 'Albania', 'paese terzo sicuro'],
  },
  {
    // Solo per la DOTTRINA: un commento può avere per oggetto il decreto di
    // attuazione in quanto tale. Nella giurisprudenza no — ogni decisione applica
    // l'attuazione italiana, quindi il tema marcava tutto e non distingueva nulla
    // (tolto dalle schede di giurisprudenza l'11.09.2026).
    slug: 'attuazione-italiana',
    label: 'Attuazione italiana',
    aliases: ['d.l. 100/2026', 'decreto-legge 100/2026', 'legge di conversione', 'A.S. 1939'],
  },
];
