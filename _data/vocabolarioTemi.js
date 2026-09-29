// Vocabolario controllato dei macro-temi per giurisprudenza, circolari e dottrina.
// Ogni scheda usa in `temi:` SOLO le label qui elencate (verifica: npm run temi-check).
// `en` / `fr`: la label mostrata nelle versioni tradotte (le schede usano sempre `label`).
// `aliases` tiene traccia dei vecchi tag assorbiti, per riferimento e per il check.
module.exports = [
  {
    slug: 'accesso-alla-procedura',
    label: 'Accesso alla procedura',
    en: 'Access to the procedure',
    fr: 'Accès à la procédure',
    aliases: ['manifestazione di volontà', 'registrazione', 'formalizzazione',
      'attestazione di manifestazione', 'fotosegnalamento', 'appuntamenti', 'termini',
      'ritardo nella manifestazione', 'Questura', 'accesso ai diritti'],
  },
  {
    slug: 'screening',
    label: 'Screening',
    en: 'Screening',
    fr: 'Filtrage',
    aliases: ['controlli di salute', 'sbarco', 'arrivi'],
  },
  {
    slug: 'procedura-di-frontiera',
    label: 'Procedura di frontiera',
    en: 'Border procedure',
    fr: 'Procédure à la frontière',
    aliases: ['zone di frontiera', 'hotspot', 'frontiera'],
  },
  {
    slug: 'procedure-accelerate',
    label: 'Procedure accelerate',
    en: 'Accelerated procedures',
    fr: 'Procédures accélérées',
    aliases: ['procedura accelerata'],
  },
  {
    slug: 'manifesta-infondatezza',
    label: 'Manifesta infondatezza',
    en: 'Manifestly unfounded applications',
    fr: 'Demandes manifestement infondées',
    aliases: [],
  },
  {
    slug: 'paesi-sicuri-soglia-20',
    label: 'Paesi sicuri e soglia del 20%',
    en: 'Safe countries and the 20% threshold',
    fr: 'Pays sûrs et seuil de 20 %',
    aliases: ['paesi di origine sicuri', 'paesi con riconoscimento ≤ 20%',
      'tasso di riconoscimento', 'paesi di origine', 'categorie di persone'],
  },
  {
    slug: 'trattenimento',
    label: 'Trattenimento',
    en: 'Detention',
    fr: 'Rétention',
    aliases: ['trattenimento de facto', 'libertà personale'],
  },
  {
    slug: 'obbligo-di-soggiorno',
    label: 'Obbligo di soggiorno',
    en: 'Obligation to reside',
    fr: 'Obligation de résider',
    aliases: [],
  },
  {
    slug: 'domanda-reiterata',
    label: 'Domanda reiterata',
    en: 'Subsequent applications',
    fr: 'Demandes ultérieures',
    aliases: ['inammissibilità'],
  },
  {
    slug: 'garanzie-procedurali',
    label: 'Garanzie procedurali',
    en: 'Procedural guarantees',
    fr: 'Garanties procédurales',
    aliases: ['colloquio', 'videoregistrazione', 'orientamento legale',
      'obblighi informativi', 'diritto di difesa', 'credibilità', 'onere della prova'],
  },
  {
    slug: 'vulnerabilita',
    label: 'Vulnerabilità',
    en: 'Vulnerability',
    fr: 'Vulnérabilité',
    aliases: ['tratta', 'categorie fragili', 'esigenze di accoglienza particolari'],
  },
  {
    slug: 'accoglienza',
    label: 'Accoglienza',
    en: 'Reception',
    fr: 'Accueil',
    aliases: ['CAS', 'termine di 90 giorni'],
  },
  {
    slug: 'regime-transitorio',
    label: 'Regime transitorio',
    en: 'Transitional rules',
    fr: 'Régime transitoire',
    aliases: ['disciplina transitoria', 'disciplina applicabile nel tempo', 'raccordo operativo'],
  },
  {
    slug: 'rimpatri',
    label: 'Rimpatri',
    en: 'Returns',
    fr: 'Retours',
    aliases: ['regolamento rimpatri', 'ordine di rimpatrio', 'espulsione', 'allontanamento'],
  },
  {
    slug: 'esternalizzazione',
    label: 'Esternalizzazione',
    en: 'Externalisation',
    fr: 'Externalisation',
    aliases: ['Protocollo Italia-Albania', 'Albania', 'paese terzo sicuro'],
  },
  {
    // Solo per la DOTTRINA: un commento può avere per oggetto il decreto di
    // attuazione in quanto tale. Nella giurisprudenza no — ogni decisione applica
    // l'attuazione italiana, quindi il tema marcava tutto e non distingueva nulla
    // (tolto dalle schede di giurisprudenza l'11.09.2026).
    slug: 'attuazione-italiana',
    label: 'Attuazione italiana',
    en: 'Italian implementation',
    fr: 'Mise en œuvre italienne',
    aliases: ['d.l. 100/2026', 'decreto-legge 100/2026', 'legge di conversione', 'A.S. 1939'],
  },
];
