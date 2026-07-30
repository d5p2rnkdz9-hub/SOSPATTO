#!/usr/bin/env python3
"""
oscura_pdf.py — Oscuramento (redaction) IRREVERSIBILE di PDF per la pubblicazione
delle schede di giurisprudenza/circolari su SOS Patto.

Perché esiste: disegnare un rettangolo nero NON basta. Se il box è
semitrasparente, o se sotto resta il testo/immagine originale, il dato personale
è ancora leggibile o estraibile (è esattamente il difetto che si era presentato
sul decreto Trib. Caltanissetta 1137/2026). Questo script usa le VERE redaction
di PyMuPDF: `add_redact_annot` + `apply_redactions(images=PDF_REDACT_IMAGE_PIXELS)`,
che rimuovono il testo sottostante E anneriscono i pixel dell'immagine. Il
risultato non è recuperabile.

Copre due casi:
  • PDF con testo selezionabile → rileva e oscura email, codici fiscali, date,
    telefoni e i nomi passati con --nomi (ricerca sul layer di testo).
  • PDF scansionati (solo immagine), tipici dei provvedimenti → modalità
    --riscura: individua i box già disegnati (anche semitrasparenti) e li rende
    opachi cancellando i pixel sotto; in più accetta box manuali con --box.

Uso tipico (scansione con box semitrasparenti da rendere opachi):
    python3 scripts/oscura_pdf.py sorgente.pdf \
        public/allegati/giurisprudenza/trib-x-2026.pdf --riscura --verifica

Uso con nomi su PDF testuale:
    python3 scripts/oscura_pdf.py sorgente.pdf out.pdf --nomi "HOSSAIN Sabbir" --verifica

Box manuale (pagina 1-indexed, coordinate in punti x0,y0,x1,y1):
    ... --box 1:56,378,161,392 --box 4:145,74,257,87

Dipendenze: pip install PyMuPDF numpy --break-system-packages
"""
import argparse
import re
import sys

import fitz  # PyMuPDF

try:
    import numpy as np
except ImportError:
    np = None

# Dati personali su PDF con testo selezionabile.
PATTERNS = {
    "email": r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
    "codice_fiscale": r"\b[A-Z]{6}[0-9]{2}[A-Z][0-9]{2}[A-Z][0-9]{3}[A-Z]\b",
    "data": r"\b\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4}\b",
    "telefono": r"(?:\+39|0039)?\s*\d{2,4}[\s\-]?\d{6,8}\b",
}
MARGINE = 1.6  # punti di margine attorno a ogni area oscurata


def _redigi(page, rects):
    """Aggiunge le redaction e le applica rimuovendo testo E pixel immagine."""
    for (x0, y0, x1, y1) in rects:
        page.add_redact_annot(
            fitz.Rect(x0 - MARGINE, y0 - MARGINE, x1 + MARGINE, y1 + MARGINE),
            fill=(0, 0, 0),
        )
    if rects:
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_PIXELS)
    return len(rects)


def _rileva_testo(page, nomi):
    """Aree da oscurare su una pagina con testo selezionabile."""
    rects, dettagli = [], []
    testo = page.get_text()
    termini = list(nomi)
    for nome, patt in PATTERNS.items():
        termini += [m.group() for m in re.finditer(patt, testo)]
    for termine in termini:
        if not termine.strip():
            continue
        for area in page.search_for(termine):
            rects.append((area.x0, area.y0, area.x1, area.y1))
            dettagli.append(termine[:40])
    return rects, dettagli


def _rileva_ocr(page, nomi, dpi=300):
    """Su pagina-immagine: OCR (ita) e oscura i nomi indicati + date/CF/email/tel,
    OVUNque compaiano — anche fuori dai box già disegnati (es. un anno di nascita
    lasciato scoperto). Richiede Tesseract con lingua 'ita'."""
    try:
        tp = page.get_textpage_ocr(language="ita", dpi=dpi, full=True)
    except Exception as e:  # tesseract assente o senza tessdata
        raise SystemExit(f"OCR non disponibile ({e}). Installa tesseract + lingua ita.")
    parole = page.get_text("words", textpage=tp)  # (x0,y0,x1,y1, parola, ...)
    token = {t.lower() for n in nomi for t in re.split(r"\s+", n) if t}
    rects, dettagli = [], []
    for w in parole:
        x0, y0, x1, y1, testo = w[0], w[1], w[2], w[3], w[4]
        pulita = testo.strip(" ,.;:()").lower()
        colpito = pulita in token or any(
            re.fullmatch(p, testo.strip(" ,.;:()")) for p in PATTERNS.values()
        )
        if colpito:
            rects.append((x0, y0, x1, y1))
            dettagli.append(testo[:40])
    return rects, dettagli


def _rileva_box(page, dpi=200):
    """Individua i box già disegnati (anche semitrasparenti) su pagina-immagine:
    lunghe corse orizzontali di pixel scuri senza spazi bianchi interni."""
    if np is None:
        raise SystemExit("Serve numpy per --riscura: pip install numpy --break-system-packages")
    sc = dpi / 72.0
    pix = page.get_pixmap(dpi=dpi)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    gray = img[:, :, :3].mean(axis=2)
    grezzi = []
    for y in range(pix.height):
        riga = gray[y] < 130
        x, W = 0, len(riga)
        while x < W:
            if riga[x]:
                s = x
                while x < W and riga[x]:
                    x += 1
                if x - s >= 40:  # corsa piena lunga = box, non testo (che ha buchi bianchi)
                    grezzi.append([s, y, x, y + 1])
            else:
                x += 1
    merged = []
    for b in grezzi:
        for m in merged:
            if not (b[2] < m[0] - 5 or b[0] > m[2] + 5 or b[3] < m[1] - 6 or b[1] > m[3] + 6):
                m[0], m[1] = min(m[0], b[0]), min(m[1], b[1])
                m[2], m[3] = max(m[2], b[2]), max(m[3], b[3])
                break
        else:
            merged.append(list(b))
    return [
        (m[0] / sc, m[1] / sc, m[2] / sc, m[3] / sc)
        for m in merged
        if (m[2] - m[0]) > 30
    ]


def oscura(src, out, nomi=None, riscura=False, ocr=False, box_manuali=None, verbose=True):
    nomi = nomi or []
    box_manuali = box_manuali or {}
    doc = fitz.open(src)
    tot = 0
    for i, page in enumerate(doc):
        rects = []
        if page.get_text().strip():
            r, det = _rileva_testo(page, nomi)
            rects += r
            if verbose and det:
                print(f"  pag {i+1}: testo → {', '.join(det)}")
        else:  # pagina-immagine (scansione)
            if riscura:
                r = _rileva_box(page)
                rects += r
                if verbose and r:
                    print(f"  pag {i+1}: {len(r)} box-immagine resi opachi")
            if ocr:
                r, det = _rileva_ocr(page, nomi)
                rects += r
                if verbose and det:
                    print(f"  pag {i+1}: OCR → {', '.join(det)}")
        rects += box_manuali.get(i + 1, [])
        tot += _redigi(page, rects)
    doc.save(out, garbage=4, deflate=True)
    doc.close()
    print(f"✅ {tot} aree oscurate (irreversibili) → {out}")
    return tot


def verifica(out):
    """Controllo dopo l'oscuramento. Due parti:
    1) automatico: nessun testo estraibile residuo con dati personali;
    2) UMANO (obbligatorio): rende ogni pagina in <out>_verifica/ così l'operatore
       controlla con un colpo d'occhio. L'auto-rilevamento NON garantisce da solo:
       un dato mai coperto (es. un anno di nascita nudo, fuori dai box) può restare
       visibile — in quel caso rioscura con --box PAGINA:x0,y0,x1,y1."""
    import os
    doc = fitz.open(out)
    testo = sum(len(p.get_text().strip()) for p in doc)
    print(f"🔎 testo estraibile residuo: {testo} caratteri "
          + ("(OK)" if testo == 0 else "(⚠️ controlla che non contenga dati personali)"))
    d = out + "_verifica"
    os.makedirs(d, exist_ok=True)
    for i, page in enumerate(doc):
        page.get_pixmap(dpi=150).save(os.path.join(d, f"pag{i+1}.png"))
    print(f"👁️  Anteprime in {d}/ — CONTROLLA A OCCHIO che nessun dato personale sia leggibile.")
    doc.close()


def _parse_box(valori):
    box = {}
    for v in valori or []:
        pag, coord = v.split(":")
        x0, y0, x1, y1 = (float(c) for c in coord.split(","))
        box.setdefault(int(pag), []).append((x0, y0, x1, y1))
    return box


def main(argv=None):
    ap = argparse.ArgumentParser(description="Oscuramento irreversibile di PDF (SOS Patto).")
    ap.add_argument("src", help="PDF sorgente")
    ap.add_argument("out", help="PDF di destinazione (es. public/allegati/giurisprudenza/...)")
    ap.add_argument("--nomi", nargs="*", default=[], help="Nomi/termini da oscurare (PDF con testo)")
    ap.add_argument("--riscura", action="store_true",
                    help="PDF scansionato: rende opachi i box semitrasparenti già presenti")
    ap.add_argument("--ocr", action="store_true",
                    help="PDF scansionato: OCR (ita) e oscura --nomi + date/CF/email/tel ovunque")
    ap.add_argument("--box", nargs="*", default=[],
                    help="Box manuali 'pagina:x0,y0,x1,y1' (punti, pagina 1-indexed)")
    ap.add_argument("--verifica", action="store_true", help="Controllo automatico dopo l'oscuramento")
    a = ap.parse_args(argv)
    oscura(a.src, a.out, nomi=a.nomi, riscura=a.riscura, ocr=a.ocr,
           box_manuali=_parse_box(a.box))
    if a.verifica:
        verifica(a.out)


if __name__ == "__main__":
    main()
