// Filtro per macro-temi sulle pagine elenco (giurisprudenza, circolari).
// Le card portano data-temi="slug1 slug2"; lo stato vive in ?tema=<slug>.
(function () {
  const barra = document.getElementById('temi-filtro');
  if (!barra) return;
  barra.hidden = false;

  const bottoni = Array.from(barra.querySelectorAll('.temi-filtro-btn'));
  const card = Array.from(document.querySelectorAll('.archivio-card[data-temi]'));

  function applica(slug, aggiornaUrl) {
    bottoni.forEach((b) => {
      b.classList.toggle('temi-filtro-attivo', (b.dataset.tema || '') === slug);
    });
    card.forEach((c) => {
      const temi = (c.dataset.temi || '').trim().split(/\s+/);
      c.hidden = Boolean(slug) && !temi.includes(slug);
    });
    if (aggiornaUrl) {
      const url = new URL(window.location);
      if (slug) url.searchParams.set('tema', slug);
      else url.searchParams.delete('tema');
      history.replaceState(null, '', url);
    }
  }

  bottoni.forEach((b) => {
    b.addEventListener('click', () => {
      const slug = b.dataset.tema || '';
      // ri-cliccare il tema attivo lo deseleziona
      const attivo = b.classList.contains('temi-filtro-attivo');
      applica(attivo ? '' : slug, true);
    });
  });

  const iniziale = new URLSearchParams(window.location.search).get('tema') || '';
  if (iniziale) applica(iniziale, false);
})();
