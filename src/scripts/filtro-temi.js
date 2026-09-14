// Filtri sulle pagine elenco (giurisprudenza, circolari, dottrina).
// Ogni barra `.temi-filtro` è una dimensione: `data-param` (default "tema") è il
// nome del parametro in URL e della chiave sulle card (tema → data-temi, corte →
// data-corte). Le chip portano data-valore (o il vecchio data-tema). Più barre si
// combinano in AND; lo stato vive in ?tema=<slug>&corte=<slug>; i conteggi delle
// chip si ricalcolano sul sottoinsieme selezionato dalle altre barre.
(function () {
  const barre = Array.from(document.querySelectorAll('.temi-filtro'));
  if (!barre.length) return;

  const card = Array.from(document.querySelectorAll('.archivio-card'));
  const paramDi = (barra) => barra.dataset.param || 'tema';
  const chiaveDi = (param) => (param === 'tema' ? 'temi' : param);
  const valoreDi = (btn) => (btn.dataset.valore !== undefined ? btn.dataset.valore : btn.dataset.tema) || '';
  const valoriCard = (c, param) => (c.dataset[chiaveDi(param)] || '').trim().split(/\s+/).filter(Boolean);

  const stato = {};
  const iniziali = new URLSearchParams(window.location.search);
  barre.forEach((barra) => {
    stato[paramDi(barra)] = iniziali.get(paramDi(barra)) || '';
  });

  // la card passa tutti i filtri attivi, salvo quello indicato in `escludi`
  function corrisponde(c, escludi) {
    return Object.keys(stato).every((p) => !stato[p] || p === escludi || valoriCard(c, p).includes(stato[p]));
  }

  // Su mobile la barra è una riga scorrevole: porta la chip attiva in vista.
  function centraAttivo(barra) {
    if (barra.scrollWidth <= barra.clientWidth) return;
    const attivo = barra.querySelector('.temi-filtro-attivo');
    if (!attivo) return;
    const b = barra.getBoundingClientRect();
    const a = attivo.getBoundingClientRect();
    const riduci = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    barra.scrollTo({
      left: barra.scrollLeft + (a.left - b.left) - (b.width - a.width) / 2,
      behavior: riduci ? 'auto' : 'smooth',
    });
  }

  function applica(aggiornaUrl) {
    card.forEach((c) => {
      c.hidden = !corrisponde(c);
    });
    barre.forEach((barra) => {
      const p = paramDi(barra);
      barra.querySelectorAll('.temi-filtro-btn').forEach((btn) => {
        const v = valoreDi(btn);
        btn.classList.toggle('temi-filtro-attivo', (stato[p] || '') === v);
        const n = card.filter((c) => corrisponde(c, p) && (!v || valoriCard(c, p).includes(v))).length;
        const span = btn.querySelector('.temi-filtro-n');
        if (span) span.textContent = n;
        btn.classList.toggle('temi-filtro-vuoto', n === 0 && v !== '');
      });
      centraAttivo(barra);
    });
    if (aggiornaUrl) {
      const url = new URL(window.location);
      Object.keys(stato).forEach((p) => {
        if (stato[p]) url.searchParams.set(p, stato[p]);
        else url.searchParams.delete(p);
      });
      history.replaceState(null, '', url);
    }
  }

  barre.forEach((barra) => {
    const p = paramDi(barra);
    barra.hidden = false;
    barra.querySelectorAll('.temi-filtro-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        const v = valoreDi(btn);
        // ri-cliccare la chip attiva la deseleziona
        stato[p] = stato[p] === v ? '' : v;
        applica(true);
      });
    });
  });

  applica(false);
})();
