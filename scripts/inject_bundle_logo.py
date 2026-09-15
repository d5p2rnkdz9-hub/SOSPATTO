#!/usr/bin/env python3
"""Adatta il bundle dei testi interattivi al sito SOS Patto ("brand" del bundle).

Bersaglio: public/patto-interattivo/, copiato tale e quale dalla copia di sospermesso
(~/TECH/SOSpermesso/Sito_Nuovo/public/patto-interattivo). Quella copia porta ancora
i link e la hub del sito di origine; questo script la fa diventare quella di SOS Patto:

1. TOPBAR: il link "torna alla home" (testuale, in tutte le varianti con cui arriva:
   «⌂ Patto UE» -> index.html nelle pagine UE, «⌂ SOS Permesso» -> /normativa.html nelle
   4 leggi, o gia' «⌂ SOS Patto» -> /) diventa il logo del sito cliccabile verso la home.
2. PANNELLO a comparsa: il link «⌂ Patto UE» in fondo (panel-home, verso la hub del
   bundle) diventa «⌂ SOS Patto» verso la home del sito.
3. HUB: la index.html alla radice del bundle (la home "Patto UE — testi interattivi")
   e' sostituita da un redirect a /testi.html, perche' quella hub e' stata assorbita
   dalle pagine /testi.html e /norme-italiane.html del sito. Il file resta perche'
   qualche link interno al bundle potrebbe ancora puntarci.
4. CSS: aggiunge/aggiorna il blocco marcato «sospatto:brand» nei 5 style.css (logo
   grande, font e colori della topbar, sticky riallineati).
5. CACHE-BUSTER: riscrive ?v=<hash> nel link al CSS di ogni pagina.

Rieseguibile senza danni (idempotente). Da rilanciare dopo ogni nuova copia del bundle,
insieme a retheme_blue.py e seo_bundle.py (l'ordine tra i tre non conta).
"""
import hashlib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUNDLE = ROOT / "public" / "patto-interattivo"

# --- 1. topbar: qualunque link testuale «⌂ …» con class="home" -> logo verso la home
HOME_RE = re.compile(r'<a class="home" href="[^"]*">&#8962; [^<]*</a>')
NEW_HOME = ('<a class="home" href="/">'
            '<img class="topbar-logo" src="/IMAGES/logo-header.png" alt="SOS Patto">'
            '</a>')

# --- 2. pannello: «⌂ Patto UE» (verso la hub del bundle) -> «⌂ SOS Patto» verso la home
PANEL_RE = re.compile(r'<a class="panel-home" href="[^"]*">&#8962; [^<]*</a>')
NEW_PANEL = '<a class="panel-home" href="/">&#8962; SOS Patto</a>'

# --- 3. hub del bundle -> redirect (il noindex e' gia' qui, seo_bundle.py lo rispetta)
HUB_MARK = 'http-equiv="refresh"'
HUB_REDIRECT = """<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Testi normativi — SOS Patto</title>
<!-- L'hub è stato assorbito dalle pagine /testi.html e /norme-italiane.html:
     questo file resta solo come redirect, perché i link "⌂ Patto UE" interni
     al bundle puntano ancora qui. -->
<meta http-equiv="refresh" content="0; url=/testi.html">
<link rel="canonical" href="https://www.sospatto.it/testi.html">
<meta name="robots" content="noindex">
</head>
<body>
<p>Questa pagina è stata spostata: <a href="/testi.html">vai ai testi normativi</a>.</p>
</body>
</html>
"""

# --- 4. CSS: blocco di brand marcato; se cambia viene SOSTITUITO al run successivo
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


def patch_hub(path):
    """index.html alla radice: diventa (o resta) il redirect a /testi.html."""
    text = path.read_text(encoding="utf-8")
    if HUB_MARK in text:
        return False
    path.write_text(HUB_REDIRECT, encoding="utf-8")
    return True


def patch_html(path):
    """Topbar e pannello di una pagina. Ritorna (topbar, panel) con True se cambiati,
    False se gia' a posto, None se la pagina non ha quell'elemento (es. audit.html)."""
    text = path.read_text(encoding="utf-8")
    new = text

    if 'class="topbar-logo"' in new:
        topbar = False
    else:
        new, n = HOME_RE.subn(NEW_HOME, new)
        topbar = True if n else None

    if 'class="panel-home"' not in new:
        panel = None
    else:
        new2 = PANEL_RE.sub(NEW_PANEL, new)
        panel = new2 != new
        new = new2

    if new != text:
        path.write_text(new, encoding="utf-8")
    return topbar, panel


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

    hub = BUNDLE / "index.html"
    esito_hub = "sostituita con il redirect a /testi.html" if patch_hub(hub) else "gia' redirect"
    print(f"hub:      index.html {esito_hub}")

    html_files = [p for p in BUNDLE.rglob("*.html") if "assets" not in p.parts and p != hub]
    css_files = list(BUNDLE.rglob("assets/style.css"))

    tb = {True: 0, False: 0, None: 0}
    pn = {True: 0, False: 0, None: 0}
    for p in html_files:
        topbar, panel = patch_html(p)
        tb[topbar] += 1
        pn[panel] += 1
    if tb[None] > 1 or pn[None] > 1:
        # solo audit.html non ha topbar/pannello: se sono di piu', il sorgente e' cambiato
        senza = [p.relative_to(BUNDLE) for p in html_files
                 if 'class="topbar-logo"' not in p.read_text(encoding="utf-8")]
        print(f"  ATTENZIONE: {len(senza)} pagine senza logo in topbar: "
              + ", ".join(str(s) for s in senza[:8]) + (" …" if len(senza) > 8 else ""))

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

    print(f"topbar:   {tb[True]} logo inseriti, {tb[False]} gia' a posto, {tb[None]} senza topbar (audit)")
    print(f"pannello: {pn[True]} link home riscritti, {pn[False]} gia' a posto, {pn[None]} senza pannello")
    print(f"CSS:      {css_patched}/{len(css_files)} style.css patchati; cache-buster: {rev_bumped} HTML aggiornati")


if __name__ == "__main__":
    main()
