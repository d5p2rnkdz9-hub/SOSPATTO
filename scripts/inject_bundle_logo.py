#!/usr/bin/env python3
"""Inserisce il logo del sito nella topbar del bundle dei testi interattivi.

Bersaglio: public/patto-interattivo/**/*.html (esclusi gli assets/, index.html
di redirect e audit.html), che arrivano da sospermesso con un link "torna alla
home" solo testuale (&#8962; SOS Patto). Questo script lo sostituisce con
l'immagine del logo reale del sito (IMAGES/logo-header.png, passthrough-copiata
alla radice), cosi' la topbar di ogni pagina del bundle porta il logo cliccabile
verso la home, come nel resto del sito.

Aggiunge anche la regola CSS .topbar-logo ai 5 style.css del bundle (copie
identiche, una per ciascun testo consolidato + una condivisa dagli atti UE).

Rieseguibile senza danni (idempotente): salta i file che hanno gia' .topbar-logo.
Da rilanciare dopo ogni nuova copia del bundle da sospermesso/deploy, insieme a
retheme_blue.py e seo_bundle.py.
"""
import hashlib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUNDLE = ROOT / "public" / "patto-interattivo"

OLD_HOME = '<a class="home" href="/">&#8962; SOS Patto</a>'
NEW_HOME = ('<a class="home" href="/">'
            '<img class="topbar-logo" src="/IMAGES/logo-header.png" alt="SOS Patto">'
            '</a>')

CSS_MARKER = ".topbar-logo"

# Blocco di brand marcato: se cambia, viene SOSTITUITO al run successivo
# (idempotente anche sugli aggiornamenti, non solo sulla prima iniezione).
BRAND_BEGIN = "/* sospatto:brand begin */"
BRAND_END = "/* sospatto:brand end */"
CSS_RULE = BRAND_BEGIN + """
/* logo grande + testi della topbar allineati al brand del sito
   (Poppins per i titoli, Inter per il resto, ink + blu SOS Patto) */
.topbar { padding: 6px 16px; gap: 14px; }
.topbar-logo { display: block; height: 66px; width: auto; }
.home-here { font-family: var(--head); font-size: 17px; font-weight: 700; color: var(--ink); }
.topttl { font-family: var(--sans); font-size: 13px; color: var(--muted); line-height: 1.35; }
.topttl b { color: var(--ink); }
.actnav a { font-family: var(--sans); }
/* la topbar ora e' alta ~79px: riallinea gli sticky (prima 41px) */
.toc { top: 79px; max-height: calc(100vh - 79px); }
.ext-banner { top: 79px; }
@media (max-width: 1000px) {
  .toc { top: 79px; max-height: none; }
  #toc-toggle {
    border: 2px solid var(--ink);
    background: #fff;
    border-radius: 10px;
    padding: 6px 14px;
    font-family: var(--head);
    font-size: 13px;
    font-weight: 700;
    box-shadow: var(--pop-sm);
  }
}
@media (max-width: 700px) {
  .topbar { gap: 10px; }
  .topbar-logo { height: 60px; }
  .home-here { font-size: 15px; }
  .topttl { font-size: 12px; }
  .toc { top: 73px; }
  .ext-banner { top: 73px; }
}
""" + BRAND_END + "\n"


def patch_html(path):
    text = path.read_text(encoding="utf-8")
    if 'class="topbar-logo"' in text:
        return False  # gia' fatto
    if OLD_HOME not in text:
        return None  # pagina senza topbar (index.html, audit.html)
    path.write_text(text.replace(OLD_HOME, NEW_HOME), encoding="utf-8")
    return True


def patch_css(path):
    text = path.read_text(encoding="utf-8")
    # rimuove la vecchia regola singola (versione 1 dello script)
    text2 = re.sub(r"\n?\.topbar-logo \{ display: block; height: 22px; width: auto; \}\n?", "\n", text)
    if BRAND_BEGIN in text2:
        # sostituisce il blocco marcato esistente (aggiornamento)
        text2 = re.sub(re.escape(BRAND_BEGIN) + r".*?" + re.escape(BRAND_END) + r"\n?",
                       CSS_RULE, text2, flags=re.S)
    else:
        text2 = text2.rstrip("\n") + "\n" + CSS_RULE
    if text2 == text:
        return False
    path.write_text(text2, encoding="utf-8")
    return True


def main():
    if not BUNDLE.is_dir():
        sys.exit(f"bundle non trovato: {BUNDLE}")

    html_files = [p for p in BUNDLE.rglob("*.html") if "assets" not in p.parts]
    css_files = list(BUNDLE.rglob("assets/style.css"))

    patched = skipped = untouched = 0
    for p in html_files:
        result = patch_html(p)
        if result is True:
            patched += 1
        elif result is False:
            skipped += 1
        else:
            untouched += 1

    css_patched = sum(1 for p in css_files if patch_css(p))

    # Cache-busting: il link al CSS nei file HTML porta ?v=<hash>; dopo una
    # modifica al CSS va aggiornato, altrimenti i browser (e la cache Netlify,
    # max-age 3600) continuano a servire lo stile vecchio. L'hash e' calcolato
    # dal contenuto del CSS: rieseguire lo script non cambia nulla (idempotente).
    rev_bumped = 0
    for html in html_files:
        css = html.parent / "assets" / "style.css"
        if not css.is_file():
            continue
        digest = hashlib.md5(css.read_bytes()).hexdigest()[:8]
        text = html.read_text(encoding="utf-8")
        new_text = re.sub(r'(href="assets/style\.css)(?:\?v=[0-9a-f]+)?(")',
                          r"\g<1>?v=" + digest + r"\g<2>", text)
        if new_text != text:
            html.write_text(new_text, encoding="utf-8")
            rev_bumped += 1

    print(f"CSS version bump: {rev_bumped} HTML aggiornati")
    print(f"HTML: {patched} patchati, {skipped} gia' a posto, "
          f"{untouched} senza topbar (index/audit)")
    print(f"CSS:  {css_patched}/{len(css_files)} style.css patchati")


if __name__ == "__main__":
    main()
