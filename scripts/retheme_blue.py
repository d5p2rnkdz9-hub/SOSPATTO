#!/usr/bin/env python3
"""Ri-tematizza in BLU i CSS di SOS Patto.

Due bersagli:
1. src/styles/*.css          — tema del sito (clonato da sospermesso, giallo taxi -> blu SOS)
2. public/patto-interattivo  — i 9 CSS del bundle dei testi interattivi
                               (clonati da sospermesso: teal/giallo -> blu; il ROSSO delle
                               novelle NON si tocca, e' convenzione giuridica)

Rieseguibile senza danni (idempotente): le sostituzioni sono esatte sui token sorgente.
Da rilanciare dopo ogni nuova copia del bundle da sospermesso/deploy.
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# ---- palette SOS Patto -------------------------------------------------
# primario "blu SOS": #33B1FF — vivido, testo ink #1A1A1A leggibile sopra (~7.4:1)
SITE_MAP = {
    "#FFD700": "#33B1FF",   # taxi yellow -> blu SOS (primario)
    "#FFEB3B": "#5BC5FF",   # yellow bright -> blu chiaro brillante
    "#FFF176": "#A8DDFF",   # yellow light -> tinta chiara
    "#FFC107": "#1E9BE9",   # yellow dark -> blu piu' scuro (hover)
    "#FFD54F": "#7FCBFF",   # amber 300 -> tinta media
    "#FFF9C4": "#DDF0FF",   # sfondo giallino -> sfondo azzurrino
    "rgba(255, 215, 0": "rgba(51, 177, 255",  # ombre/veli del primario
    # link teal di sospermesso -> blu link
    "#1A6B5F": "#1565C0",
    "#14564C": "#0D47A1",
    "rgba(26, 107, 95": "rgba(21, 101, 192",
    "rgba(26,107,95": "rgba(21,101,192",
}

BUNDLE_MAP = {
    # link teal -> blu link (contrasto su bianco ok)
    "#1A6B5F": "#1565C0",
    "#14564C": "#0D47A1",
    "rgba(26, 107, 95": "rgba(21, 101, 192",
    "rgba(26,107,95": "rgba(21,101,192",
    # accenti gialli -> blu
    "#FFD700": "#33B1FF",
    "#FFEB3B": "#5BC5FF",
    "#FFE082": "#A8D4FF",
    "#FFF3C4": "#DBEDFF",   # hover soft
    "#FFF8E1": "#EAF4FF",   # sfondo tenue
    # ori scuri (testo/bordi badge) -> blu scuri
    "#b08c2e": "#2E6BB0",
    "#6b5300": "#0B3D75",
}

def retheme(paths, mapping):
    changed = 0
    for p in paths:
        css = p.read_text(encoding="utf-8")
        out = css
        for old, new in mapping.items():
            # case-insensitive sui hex (nei sorgenti compaiono sia maiuscoli che minuscoli)
            out = re.sub(re.escape(old), new, out, flags=re.IGNORECASE)
        if out != css:
            p.write_text(out, encoding="utf-8")
            changed += 1
            print(f"  ritinto: {p.relative_to(ROOT)}")
    return changed

print("== tema sito ==")
site_files = sorted((ROOT / "src" / "styles").glob("*.css"))
n1 = retheme(site_files, SITE_MAP)

print("== bundle testi interattivi ==")
bundle_files = sorted((ROOT / "public" / "patto-interattivo").rglob("*.css"))
n2 = retheme(bundle_files, BUNDLE_MAP)

# verifica: nessun token giallo/teal residuo
residui = []
for p in site_files + bundle_files:
    css = p.read_text(encoding="utf-8")
    for tok in ["#FFD700", "#FFEB3B", "#FFF176", "#FFC107", "#FFD54F", "#FFF9C4",
                "#1A6B5F", "#14564C", "#FFF3C4", "#FFF8E1", "#FFE082", "#b08c2e", "#6b5300",
                "rgba(255, 215, 0", "rgba(26, 107, 95", "rgba(26,107,95"]:
        if re.search(re.escape(tok), css, re.IGNORECASE):
            residui.append((p.relative_to(ROOT), tok))

print(f"\n{n1} css sito + {n2} css bundle ritinti.")
if residui:
    print("RESIDUI NON MAPPATI:")
    for f, t in residui:
        print(f"  {f}: {t}")
    sys.exit(1)
print("OK: nessun token giallo/teal residuo.")
