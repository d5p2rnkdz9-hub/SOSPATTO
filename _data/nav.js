// Menu di navigazione. Solo italiano per ora: quando arriveranno altre lingue,
// aggiungere chiavi 'en', 'fr', ... con la stessa struttura (come su sospermesso).
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
          { label: 'Italiana', href: '/giurisprudenza.html#italiana' },
          { label: 'Europea', href: '/giurisprudenza.html#europea' },
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
};
