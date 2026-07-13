#!/usr/bin/env python3
"""Inietta i meta SEO nel bundle dei testi interattivi di SOS Patto.

Bersaglio: public/patto-interattivo/**/*.html (esclusi gli assets/).
I file del bundle arrivano da sospermesso con il solo <title> nel <head>:
questo script aggiunge, subito dopo il title, un blocco marcato
<!-- seo:begin --> ... <!-- seo:end --> con:
  - <link rel="canonical">  (per gli index.html delle sottocartelle: URL
    della directory con slash finale)
  - <meta name="description">  generata dal title (pattern diversi per
    atti UE del Patto, d.lgs. consolidati, atti esterni ext-*)
  - meta Open Graph (og:title/description/url/type/site_name/image)

Casi speciali: index.html (redirect verso /testi.html) e audit.html
ricevono SOLO <meta name="robots" content="noindex">, niente canonical/og.

Rieseguibile senza danni (idempotente): se un file ha gia' il blocco
seo:begin/end lo sostituisce; se ha gia' canonical/description/robots
propri (fuori dal blocco) non tocca nulla.
Da rilanciare dopo ogni nuova copia del bundle da sospermesso/deploy,
insieme a retheme_blue.py.
"""
import html
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUNDLE = ROOT / "public" / "patto-interattivo"
BASE_URL = "https://www.sospatto.it/patto-interattivo/"
OG_IMAGE = "https://www.sospatto.it/IMAGES/og-image.png"

# file (relativi al bundle) da marcare solo noindex, senza canonical/og
NOINDEX_ONLY = {"index.html", "audit.html"}

SEO_BEGIN = "<!-- seo:begin -->"
SEO_END = "<!-- seo:end -->"

TITLE_RE = re.compile(r"<title>(.*?)</title>", re.DOTALL | re.IGNORECASE)
BLOCK_RE = re.compile(re.escape(SEO_BEGIN) + r".*?" + re.escape(SEO_END) + r"\n?",
                      re.DOTALL)


def esc(s):
    """Escapa per attributi HTML (virgolette e &, senza toccare gli accenti)."""
    return html.escape(s, quote=True)


def make_description(title, rel):
    """Genera la description dal <title>, con pattern per tipo di pagina."""
    # i title del bundle sono "Nome — Riferimento atto" (em dash)
    parts = [p.strip() for p in title.split("—", 1)]
    nome = parts[0]
    resto = parts[1] if len(parts) > 1 else ""

    if rel.startswith("dlgs-"):
        # testi consolidati italiani, modifiche evidenziate
        coda = f" ({resto})" if resto else ""
        return (f"Testo consolidato interattivo del {nome} con le modifiche "
                f"evidenziate{coda} — norme italiane collegate al Patto UE "
                f"su migrazione e asilo, su SOS Patto.")

    if rel.startswith("ext-"):
        # decisioni/atti collegati, esterni al Patto
        return (f"Testo interattivo e navigabile di {nome}, atto collegato "
                f"al Patto UE su migrazione e asilo, su SOS Patto.")

    # atti UE del Patto: "Direttiva accoglienza — Direttiva (UE) 2024/1346"
    if resto:
        return (f"Testo interattivo e navigabile della {resto} ({nome}) — "
                f"Patto UE su migrazione e asilo, su SOS Patto.")
    return (f"Testo interattivo e navigabile di {nome} — Patto UE su "
            f"migrazione e asilo, su SOS Patto.")


def canonical_url(rel):
    """URL canonico: per gli index.html delle sottocartelle, la directory."""
    if rel.endswith("/index.html"):
        return BASE_URL + rel[: -len("index.html")]
    return BASE_URL + rel


def build_block(title, rel):
    url = canonical_url(rel)
    desc = make_description(title, rel)
    lines = [
        SEO_BEGIN,
        f'<link rel="canonical" href="{esc(url)}">',
        f'<meta name="description" content="{esc(desc)}">',
        f'<meta property="og:title" content="{esc(title)}">',
        f'<meta property="og:description" content="{esc(desc)}">',
        f'<meta property="og:url" content="{esc(url)}">',
        '<meta property="og:type" content="article">',
        '<meta property="og:site_name" content="SOS Patto">',
        f'<meta property="og:image" content="{OG_IMAGE}">',
        SEO_END,
    ]
    return "\n".join(lines)


def process(path):
    """Ritorna uno di: 'iniettato', 'aggiornato', 'gia_ok', 'noindex', 'skip'."""
    rel = path.relative_to(BUNDLE).as_posix()
    src = path.read_text(encoding="utf-8")

    m = TITLE_RE.search(src)
    if not m:
        print(f"  ATTENZIONE: nessun <title> in {rel}, salto")
        return "skip"
    title = re.sub(r"\s+", " ", m.group(1)).strip()

    # -- casi speciali: solo noindex ------------------------------------
    if rel in NOINDEX_ONLY:
        if re.search(r'name="robots"', src):
            return "gia_ok"
        block = f'{SEO_BEGIN}\n<meta name="robots" content="noindex">\n{SEO_END}'
        out = src[: m.end()] + "\n" + block + src[m.end():]
        path.write_text(out, encoding="utf-8")
        return "noindex"

    # -- pagine normali: canonical + description + og -------------------
    block = build_block(title, rel)

    if SEO_BEGIN in src:
        # blocco gia' presente: rimpiazza solo se cambiato
        new = BLOCK_RE.sub(block + "\n", src, count=1)
        if new == src:
            return "gia_ok"
        path.write_text(new, encoding="utf-8")
        return "aggiornato"

    # canonical/description propri gia' presenti fuori dal blocco: non tocco
    if re.search(r'rel="canonical"', src) or re.search(r'name="description"', src):
        return "gia_ok"

    out = src[: m.end()] + "\n" + block + src[m.end():]
    path.write_text(out, encoding="utf-8")
    return "iniettato"


def main():
    if not BUNDLE.is_dir():
        sys.exit(f"cartella non trovata: {BUNDLE}")

    files = sorted(p for p in BUNDLE.rglob("*.html")
                   if "assets" not in p.relative_to(BUNDLE).parts)

    tally = {"iniettato": 0, "aggiornato": 0, "gia_ok": 0, "noindex": 0, "skip": 0}
    for p in files:
        esito = process(p)
        tally[esito] += 1
        if esito in ("iniettato", "aggiornato", "noindex"):
            print(f"  {esito}: {p.relative_to(ROOT)}")

    print(f"\n{len(files)} file processati: "
          f"{tally['iniettato']} iniettati, {tally['aggiornato']} aggiornati, "
          f"{tally['gia_ok']} gia' a posto, {tally['noindex']} noindex, "
          f"{tally['skip']} saltati.")


if __name__ == "__main__":
    main()
