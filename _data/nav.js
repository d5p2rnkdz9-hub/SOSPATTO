// Menu di navigazione, una chiave per lingua (come su sospermesso). Le voci verso
// pagine solo in italiano (diagramma) portano alla pagina italiana, segnalata con «(IT)».
module.exports = {
  it: {
    dropdowns: [
      {
        label: 'Normativa',
        href: '/testi.html',
        items: [
          { label: 'Regolamenti e Direttive UE', href: '/testi.html' },
          { label: 'Leggi italiane', href: '/norme-italiane.html' },
          { label: 'Circolari e SOP', href: '/circolari.html' },
        ],
      },
      {
        label: 'Giurisprudenza e dottrina',
        href: '/giurisprudenza.html',
        items: [
          { label: 'Giurisprudenza europea', href: '/giurisprudenza-europea.html' },
          { label: 'Giurisprudenza italiana', href: '/giurisprudenza.html' },
          { label: 'Commenti e dottrina', href: '/dottrina.html' },
        ],
      },
      {
        label: 'Strumenti interattivi',
        href: '/diagramma.html',
        items: [
          { label: 'Diagramma procedure', href: '/diagramma.html' },
          { label: 'Test interattivi', href: 'https://app.sospatto.it', external: true },
        ],
      },
      {
        label: 'Siti partner',
        href: 'https://www.sospermesso.it',
        items: [
          { label: 'SOS Permesso', href: 'https://www.sospermesso.it', external: true },
          { label: 'Studio Legale Oltre', href: 'https://studiolegaleoltre.org', external: true },
        ],
      },
      {
        label: 'Contatti',
        href: '/il-progetto.html',
        items: [
          { label: 'Il progetto', href: '/il-progetto.html' },
          { label: 'Scrivici', href: 'mailto:info@studiolegaleoltre.org', external: true },
        ],
      },
    ],
  },
  en: {
    dropdowns: [
      {
        label: 'Legislation',
        href: '/en/testi.html',
        items: [
          { label: 'EU Regulations and Directives', href: '/en/testi.html' },
          { label: 'Italian legislation', href: '/en/norme-italiane.html' },
          { label: 'Circulars and SOPs', href: '/en/circolari.html' },
        ],
      },
      {
        label: 'Case law and commentary',
        href: '/en/giurisprudenza.html',
        items: [
          { label: 'European case law', href: '/en/giurisprudenza-europea.html' },
          { label: 'Italian case law', href: '/en/giurisprudenza.html' },
          { label: 'Commentary and scholarship', href: '/en/dottrina.html' },
        ],
      },
      {
        label: 'Interactive tools',
        href: '/diagramma.html',
        items: [
          { label: 'Procedure diagram (IT)', href: '/diagramma.html' },
          { label: 'Interactive tests (IT)', href: 'https://app.sospatto.it', external: true },
        ],
      },
      {
        label: 'Partner sites',
        href: 'https://www.sospermesso.it',
        items: [
          { label: 'SOS Permesso', href: 'https://www.sospermesso.it/en/', external: true },
          { label: 'Studio Legale Oltre', href: 'https://studiolegaleoltre.org', external: true },
        ],
      },
      {
        label: 'Contact',
        href: '/en/il-progetto.html',
        items: [
          { label: 'The project', href: '/en/il-progetto.html' },
          { label: 'Write to us', href: 'mailto:info@studiolegaleoltre.org', external: true },
        ],
      },
    ],
  },
  fr: {
    dropdowns: [
      {
        label: 'Législation',
        href: '/fr/testi.html',
        items: [
          { label: "Règlements et directives de l'UE", href: '/fr/testi.html' },
          { label: 'Législation italienne', href: '/fr/norme-italiane.html' },
          { label: 'Circulaires et SOP', href: '/fr/circolari.html' },
        ],
      },
      {
        label: 'Jurisprudence et doctrine',
        href: '/fr/giurisprudenza.html',
        items: [
          { label: 'Jurisprudence européenne', href: '/fr/giurisprudenza-europea.html' },
          { label: 'Jurisprudence italienne', href: '/fr/giurisprudenza.html' },
          { label: 'Commentaires et doctrine', href: '/fr/dottrina.html' },
        ],
      },
      {
        label: 'Outils interactifs',
        href: '/diagramma.html',
        items: [
          { label: 'Diagramme des procédures (IT)', href: '/diagramma.html' },
          { label: 'Tests interactifs (IT)', href: 'https://app.sospatto.it', external: true },
        ],
      },
      {
        label: 'Sites partenaires',
        href: 'https://www.sospermesso.it',
        items: [
          { label: 'SOS Permesso', href: 'https://www.sospermesso.it/fr/', external: true },
          { label: 'Studio Legale Oltre', href: 'https://studiolegaleoltre.org', external: true },
        ],
      },
      {
        label: 'Contact',
        href: '/fr/il-progetto.html',
        items: [
          { label: 'Le projet', href: '/fr/il-progetto.html' },
          { label: 'Écrivez-nous', href: 'mailto:info@studiolegaleoltre.org', external: true },
        ],
      },
    ],
  },
};
