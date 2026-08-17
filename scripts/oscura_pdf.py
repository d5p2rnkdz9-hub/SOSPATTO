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

# ─────────────────────────────────────────────────────────────────────────────
# IDENTIFICATIVI OSCURATI SEMPRE — anche con --solo-nomi.
#
# Perché: --solo-nomi nasce per non annerire le date processuali dei provvedimenti
# nativi digitali, ma disattivando TUTTI i pattern lasciava passare identificativi
# che non hanno mai valore informativo in una scheda. È l'errore che si è ripetuto:
# il C.U.I. in chiaro accanto al nome coperto (Trib. Firenze 9251-1/2026 e Trib.
# Bologna 12435-1/2026, agosto 2026; e prima, il C.U.I. di Trib. Palermo 8694).
# Questi pattern quindi NON si disattivano: un C.U.I., un codice fiscale, una mail,
# un telefono o una data di nascita non servono mai al lettore della scheda.
#
# Ogni pattern ha UN gruppo di cattura: è quello che viene effettivamente oscurato,
# così il contesto ("nato a Bogotà il", "CUI:") resta leggibile e la pagina resta
# comprensibile.
# ─────────────────────────────────────────────────────────────────────────────
PATTERNS_SEMPRE = {
    # C.U.I. con etichetta: «(CUI: 07J37ZV)», «C.U.I. 07JAOIX»
    "cui_etichettato": r"C\.?\s?U\.?\s?I\.?\s*[:.]?\s*([A-Z0-9]{5,10})\b",
    "codice_fiscale": r"\b([A-Z]{6}[0-9]{2}[A-Z][0-9]{2}[A-Z][0-9]{3}[A-Z])\b",
    "email": r"\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b",
    # Telefono italiano: prefisso +39 facoltativo, poi un numero che inizia per 0
    # (fisso) o 3 (mobile). Il vincolo sulla prima cifra evita di prendere per numeri
    # di telefono le lunghe corse di cifre dei PDF con font-subset illeggibile.
    "telefono": r"(?:(?:\+39|0039)\s*)?\b((?:0|3)\d{1,3}[\s\-]?\d{6,8})\b",
    # Data di nascita: solo se preceduta dal contesto («nato/nata a … il GG/MM/AAAA»),
    # così si copre il dato personale senza toccare le date della decisione.
    # Il \b INIZIALE è indispensabile: senza, «nato» viene trovato dentro «combinato»
    # e il pattern annerisce la data del D.L. citato nella formula di firma digitale
    # («art. 4 del D.L. 29/12/2009» nei decreti di Palermo).
    "data_di_nascita": (
        r"\b(?:nat[oa]|nascit[ao])\b[^,;\n]{0,60}?"
        r"\b(\d{1,2}\s*[/.\-]\s*\d{1,2}\s*[/.\-]\s*\d{2,4})\b"
    ),
    # ID dei gestionali lasciati negli URL a piè di pagina
    "id_gestionale": r"[?&](?:id|idPratica|pratica|idDoc|fascicolo)=([A-Za-z0-9._-]{4,})",
}

# C.U.I. senza etichetta (07J37ZV, 07JAOIX, 07J36V2): 2 cifre + lettera + 4
# alfanumerici. Cercato SOLO nelle pagine che contengono anche la sigla «CUI», perché
# la forma è troppo generica: sui PDF con font-subset illeggibile il testo estratto è
# spazzatura maiuscola e la stessa forma ricorre per caso (es. «46SS34P» in Trib.
# Bologna 11250/2026), con il rischio di annerire testo visibile e innocuo.
CUI_NUDO = r"\b(\d{2}[A-Z][A-Z0-9]{4})\b"
CUI_ETICHETTA = r"C\.?\s?U\.?\s?I\.?\b"

# Oscurati SOLO quando non si usa --solo-nomi (tipicamente sulle scansioni): su un
# provvedimento nativo digitale le date sono processuali — data della decisione, di
# pubblicazione, delle norme citate — e devono restare leggibili.
PATTERNS_OPZIONALI = {
    "data": r"\b(\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4})\b",
}

# Sottoinsieme applicabile all'OCR, che lavora parola per parola e non vede il
# contesto: qui le date si oscurano tutte, perché su una scansione di provvedimento
# una data isolata è più spesso una data di nascita che una data processuale.
PATTERNS_PAROLA = {
    # qui il C.U.I. nudo si può usare senza restrizioni: l'OCR produce testo reale,
    # non la spazzatura maiuscola dei PDF con font-subset
    "cui": CUI_NUDO,
    "codice_fiscale": PATTERNS_SEMPRE["codice_fiscale"],
    "email": PATTERNS_SEMPRE["email"],
    "telefono": PATTERNS_SEMPRE["telefono"],
    "data": PATTERNS_OPZIONALI["data"],
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


def _rileva_testo(page, nomi, solo_nomi=False, tieni_contatti=False):
    """Aree da oscurare su una pagina con testo selezionabile.

    Con solo_nomi=True si oscurano soltanto i termini passati in --nomi: serve per i
    provvedimenti nativi digitali, dove l'unico dato personale è il nome della parte e
    le date sono processuali (data della decisione, data di pubblicazione, date delle
    norme citate) e devono restare leggibili."""
    rects, dettagli = [], []
    testo = page.get_text()

    # (termine, etichetta) — i nomi passati a mano, poi gli identificativi.
    termini = [(n, "nome") for n in nomi]

    attivi = dict(PATTERNS_SEMPRE)          # mai disattivabili
    if re.search(CUI_ETICHETTA, testo):     # solo dove i C.U.I. sono effettivamente in uso
        attivi["cui"] = CUI_NUDO
    if not solo_nomi:
        attivi.update(PATTERNS_OPZIONALI)
    if tieni_contatti:                      # solo per le circolari: vedi --tieni-contatti
        attivi.pop("email", None)
        attivi.pop("telefono", None)
    for nome, patt in attivi.items():
        for m in re.finditer(patt, testo):
            # ogni pattern ha un gruppo di cattura: si oscura solo quello, non il contesto
            termini.append((m.group(1) if m.groups() else m.group(), nome))

    for termine, etichetta in termini:
        if not termine or not termine.strip():
            continue
        for area in page.search_for(termine):
            rects.append((area.x0, area.y0, area.x1, area.y1))
            dettagli.append(f"{termine[:40]} [{etichetta}]")
    return rects, dettagli


def _rileva_ocr(page, nomi, dpi=300, solo_nomi=False):
    """Su pagina-immagine: OCR (ita) e oscura i nomi indicati + C.U.I./CF/email/tel,
    OVUNque compaiano — anche fuori dai box già disegnati (es. un anno di nascita
    lasciato scoperto). Richiede Tesseract con lingua 'ita'.

    Con solo_nomi=True le DATE non vengono oscurate. Serve sulle scansioni dei
    provvedimenti in cui le date sono processuali e portano il senso della decisione
    (ingresso in Italia, manifestazione di volontà, C3, data del decreto): oscurarle
    tutte rende il documento inutilizzabile. In quel caso la data di nascita, se c'è,
    va coperta con un --box mirato."""
    try:
        tp = page.get_textpage_ocr(language="ita", dpi=dpi, full=True)
    except Exception as e:  # tesseract assente o senza tessdata
        raise SystemExit(f"OCR non disponibile ({e}). Installa tesseract + lingua ita.")
    parole = page.get_text("words", textpage=tp)  # (x0,y0,x1,y1, parola, ...)
    token = {t.lower() for n in nomi for t in re.split(r"\s+", n) if t}
    rects, dettagli = [], []
    for w in parole:
        x0, y0, x1, y1, testo = w[0], w[1], w[2], w[3], w[4]
        pulita = testo.strip(" ,.;:()")
        etichetta = "nome" if pulita.lower() in token else None
        if etichetta is None:
            for nome, patt in PATTERNS_PAROLA.items():
                if nome == "data" and solo_nomi:
                    continue  # date processuali: restano leggibili
                if re.fullmatch(patt, pulita):
                    etichetta = nome
                    break
        if etichetta:
            rects.append((x0, y0, x1, y1))
            dettagli.append(f"{testo[:40]} [{etichetta}]")
    return rects, dettagli


ALTEZZA_MIN_BOX = 5.0  # punti: sotto questa soglia è una sottolineatura, non un box


def _rileva_box(page, dpi=200):
    """Individua i box già disegnati (anche semitrasparenti) su pagina-immagine:
    lunghe corse orizzontali di pixel scuri senza spazi bianchi interni.

    Filtra per ALTEZZA oltre che per larghezza: una sottolineatura in grassetto è
    anch'essa una lunga corsa di pixel scuri, ma è alta 1-3 px. Senza questo filtro
    veniva presa per un box e anneriva mezza riga di testo — è successo sulla
    sottolineatura di «Manda alla Cancelleria...» nei decreti Trib. Bologna del
    12.08.2026."""
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
        if (m[2] - m[0]) > 30 and (m[3] - m[1]) / sc >= ALTEZZA_MIN_BOX
    ]


def oscura(src, out, nomi=None, riscura=False, ocr=False, box_manuali=None,
           solo_nomi=False, tieni_contatti=False, verbose=True):
    nomi = nomi or []
    box_manuali = box_manuali or {}
    doc = fitz.open(src)
    tot = 0
    for i, page in enumerate(doc):
        rects = []
        if page.get_text().strip():
            r, det = _rileva_testo(page, nomi, solo_nomi=solo_nomi,
                                   tieni_contatti=tieni_contatti)
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
                r, det = _rileva_ocr(page, nomi, solo_nomi=solo_nomi)
                rects += r
                if verbose and det:
                    print(f"  pag {i+1}: OCR → {', '.join(det)}")
        rects += box_manuali.get(i + 1, [])
        tot += _redigi(page, rects)
    doc.save(out, garbage=4, deflate=True)
    doc.close()
    print(f"✅ {tot} aree oscurate (irreversibili) → {out}")
    return tot


def verifica(out, anteprime=True):
    """Controllo dopo l'oscuramento. Tre parti:
    1) automatico: quanto testo resta estraibile;
    2) automatico e SEMPRE ATTIVO: nessun identificativo di PATTERNS_SEMPRE deve
       essere ancora estraibile (C.U.I., codice fiscale, email, telefono, data di
       nascita);
    3) UMANO (obbligatorio sulle scansioni, con anteprime=True): rende ogni pagina in
       <out>_verifica/ così l'operatore controlla con un colpo d'occhio. Il controllo
       automatico NON basta: un dato che sta solo nei pixel (scansione senza livello
       testo) non è estraibile e quindi non viene segnalato, ma è perfettamente
       leggibile — in quel caso rioscura con --ocr o --box PAGINA:x0,y0,x1,y1."""
    import os
    doc = fitz.open(out)
    testo = sum(len(p.get_text().strip()) for p in doc)
    print(f"🔎 testo estraibile residuo: {testo} caratteri "
          + ("(OK)" if testo == 0 else "(⚠️ controlla che non contenga dati personali)"))

    # Ricontrollo mirato: nessun identificativo delle classi "sempre" deve essere
    # ancora estraibile. Se ne resta uno, l'oscuramento è da rifare (di norma perché
    # il dato sta in una pagina-immagine e serve --ocr o un --box manuale).
    residui = []
    for i, page in enumerate(doc):
        t = page.get_text()
        for nome, patt in PATTERNS_SEMPRE.items():
            for m in re.finditer(patt, t):
                residui.append((i + 1, nome, (m.group(1) if m.groups() else m.group())[:40]))
    if residui:
        print("❌ IDENTIFICATIVI ANCORA ESTRAIBILI — non pubblicare:")
        for pag, nome, val in residui:
            print(f"     pag {pag}: {nome} → {val}")
    else:
        print("✅ nessun C.U.I./codice fiscale/email/telefono/data di nascita estraibile")

    if anteprime:
        d = out + "_verifica"
        os.makedirs(d, exist_ok=True)
        for i, page in enumerate(doc):
            page.get_pixmap(dpi=150).save(os.path.join(d, f"pag{i+1}.png"))
        print(f"👁️  Anteprime in {d}/ — CONTROLLA A OCCHIO che nessun dato personale sia leggibile.")
    doc.close()
    return residui


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
    ap.add_argument("--solo-nomi", action="store_true",
                    help="PDF nativo digitale: oscura SOLO i --nomi e le date PROCESSUALI restano "
                         "leggibili. NB: C.U.I., codici fiscali, email, telefoni e date di nascita "
                         "vengono oscurati comunque (PATTERNS_SEMPRE)")
    ap.add_argument("--tieni-contatti", action="store_true",
                    help="NON oscurare email e telefoni. Serve SOLO per circolari e atti di prassi "
                         "il cui contenuto utile sono i contatti istituzionali (numeri verdi, PEC "
                         "delle questure, referenti antitratta). MAI su un provvedimento")
    ap.add_argument("--verifica", action="store_true",
                    help="Anteprime PNG per il controllo a occhio (il ricontrollo automatico degli "
                         "identificativi gira sempre)")
    a = ap.parse_args(argv)
    oscura(a.src, a.out, nomi=a.nomi, riscura=a.riscura, ocr=a.ocr,
           box_manuali=_parse_box(a.box), solo_nomi=a.solo_nomi,
           tieni_contatti=a.tieni_contatti)
    # Il ricontrollo sugli identificativi gira SEMPRE: è l'unico modo per non
    # ripubblicare per la terza volta un C.U.I. in chiaro. --verifica aggiunge le
    # anteprime PNG, che restano indispensabili per le scansioni.
    verifica(a.out, anteprime=a.verifica)


if __name__ == "__main__":
    main()
