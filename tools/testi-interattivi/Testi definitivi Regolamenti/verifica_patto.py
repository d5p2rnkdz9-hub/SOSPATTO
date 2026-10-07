# -*- coding: utf-8 -*-
"""
Verificatore indipendente del sito "Patto interattivo".

Non riusa la logica di build_patto_interattivo.py: rilegge le pagine GENERATE
e controlla, link per link:
  - ancore: ogni href interno punta a un id esistente;
  - coerenza testo/target: i numeri visibili nel testo del link (articolo,
    paragrafo, atto, considerando, allegato, capo/parte) corrispondono ai
    data-attribute e all'href;
  - dati tooltip: ogni link con data-act/data-art/data-par/data-rct ha contenuto
    non vuoto in data.js (o data-ext/<key>.js), così l'hover mostra testo inline;
  - classificazione dei casi che richiedono verifica semantica (anafore
    "tale/detto/stesso/medesimo regolamento", rinvii senza coda con altro atto
    citato vicino, link dentro virgolettati di modifica, ecc.).

Output in "verifica/":
  links_all.jsonl     tutti i link con contesto annotato
  suspects.jsonl      sottoinsieme da rivedere semanticamente
  problems.json       errori deterministici
  summary.txt         statistiche
"""

import json
import re
import sys
import unicodedata
from pathlib import Path
from collections import defaultdict, Counter

from bs4 import BeautifulSoup, Tag

BASE = Path(__file__).parent
SITE = BASE / "Patto interattivo"
OUTDIR = BASE / "verifica"
OUTDIR.mkdir(exist_ok=True)

CORPUS_KEYS = ["1346", "1347", "1348", "1349", "1350", "1351", "1352", "1356", "1358", "1359"]
CORPUS_TYP = {"1346": "dir"}  # tutti gli altri reg
ORD_LETTER = {"bis": "a", "ter": "b", "quater": "c", "quinquies": "d", "sexies": "e",
              "septies": "f", "octies": "g", "novies": "h", "nonies": "h",
              "decies": "i", "undecies": "j", "duodecies": "k", "terdecies": "l"}
ORDS = "|".join(ORD_LETTER)


def norm(s):
    s = unicodedata.normalize("NFC", s)
    return s.replace(" ", " ")


# ---------------------------------------------------------------- dati tooltip

def load_pacto_data():
    txt = (SITE / "assets" / "data.js").read_text(encoding="utf-8")
    m = re.match(r"window\.PACTO=(.*);window\.PACTO_V=.*$", txt, re.S)
    if not m:
        sys.exit("formato data.js inatteso")
    data = json.loads(m.group(1))
    ext_files = {}
    for fp in sorted((SITE / "assets" / "data-ext").glob("*.js")):
        t = fp.read_text(encoding="utf-8")
        m = re.match(r'window\.PACTO\.acts\["([^"]+)"\]=(.*);\s*$', t, re.S)
        if not m:
            print(f"AVVISO: formato inatteso {fp.name}")
            continue
        ext_files[m.group(1)] = json.loads(m.group(2))
    return data, ext_files


# ---------------------------------------------------------------- id per pagina

def collect_ids():
    ids = {}
    for fp in sorted(SITE.glob("*.html")):
        if fp.name in ("audit.html",):
            continue
        soup = BeautifulSoup(fp.read_text(encoding="utf-8"), "lxml")
        ids[fp.name] = {el.get("id") for el in soup.find_all(id=True)}
    return ids


# ---------------------------------------------------------------- estrazione

def target_label(a):
    """forma breve del bersaglio di un link xref, per l'annotazione del contesto."""
    d = a.attrs
    act = d.get("data-act")
    href = a.get("href", "")
    if "ext" in (a.get("class") or []):
        return "WEB:" + href.replace("https://eur-lex.europa.eu/", "")
    parts = []
    if act:
        parts.append(act)
    if d.get("data-art"):
        parts.append("art" + d["data-art"])
    if d.get("data-par"):
        parts.append("par" + d["data-par"])
    if d.get("data-rct"):
        parts.append("cons" + d["data-rct"])
    if d.get("data-anx"):
        parts.append("anx" + d["data-anx"])
    if d.get("data-sec"):
        parts.append(d["data-sec"])
    if not parts:
        parts.append(href)
    return ":".join(parts) if parts else "?"


def annotate_block(block, current):
    """testo del blocco con ogni xref annotato; il link in esame marcato ▶…◀."""
    out = []

    def walk(el):
        for child in el.children:
            if isinstance(child, Tag):
                if child.name == "a" and "xref" in (child.get("class") or []):
                    t = norm(child.get_text())
                    if child is current:
                        out.append(f"▶{t}‖{target_label(child)}◀")
                    else:
                        out.append(f"⟦{t}‖{target_label(child)}⟧")
                elif child.name in ("script", "style"):
                    continue
                else:
                    walk(child)
            else:
                out.append(norm(str(child)))

    walk(block)
    return re.sub(r"\s+", " ", "".join(out)).strip()


def find_block(a):
    """blocco di contesto: il <p> (o td/div) che contiene il link; se corto, sale."""
    el = a
    block = None
    for p in a.parents:
        if not isinstance(p, Tag):
            break
        if p.name == "p":
            block = p
            break
        if p.name in ("td", "li", "div") and block is None and p.name != "div":
            block = p
            break
    if block is None:
        block = a.parent
    # se il blocco è corto (es. cella di tabella con solo il numero), sali
    hops = 0
    while len(block.get_text(" ", strip=True)) < 110 and hops < 3:
        nxt = block.parent
        if not isinstance(nxt, Tag) or nxt.name in ("body", "html", "[document]", "main"):
            break
        block = nxt
        hops += 1
    return block


def scope_of(a):
    art = par_div = rct = anx = None
    quote = False
    for p in a.parents:
        if not isinstance(p, Tag):
            break
        classes = p.get("class") or []
        if "oj-quotation" in classes:
            quote = True
        pid = p.get("id", "")
        if re.match(r"^\d{3}\.\d{3}[A-Z]?$", pid) and par_div is None:
            par_div = pid
        if pid.startswith("art_") and art is None:
            art = pid
        if pid.startswith("rct_") and rct is None:
            rct = pid
        if pid.startswith("anx") and anx is None:
            anx = pid
    return art, par_div, rct, anx, quote


# ---------------------------------------------------------------- controlli

RE_T_ART = re.compile(r"articol[oi]\s+(?:da\s+)?(\d{1,3})\s*[\s-]?(" + ORDS + r")?\b", re.IGNORECASE)
RE_T_PAR = re.compile(r"paragraf[oi]\s+(\d{1,3})", re.IGNORECASE)
RE_T_BARE = re.compile(r"^\s*(\d{1,3})\s*$")
RE_T_ACT = re.compile(
    r"(regolament|direttiv|decision)\w*"
    r"(?:\s+(?:di\s+esecuzione|delegat[oa]|quadro))?"
    r"\s*(?:\(\s*(?:UE,?\s*Euratom|UE|CE|CEE|EU)\s*\))?"
    r"\s*((?:n\.\s*)?)"
    r"(\d{1,4})/(\d{1,4})", re.IGNORECASE)
RE_T_RCT = re.compile(r"considerando\s+(\d{1,3})", re.IGNORECASE)
RE_T_ANX = re.compile(r"allegat[oi]\s+([IVX]+|\d+)", re.IGNORECASE)
RE_T_SEC = re.compile(r"\b(capo|parte)\s+([IVX]+)", re.IGNORECASE)

RE_ANAPH = re.compile(
    r"\b(?:tale|tali|dett[oa]|medesim[oa]|stess[oa])\s+(?:regolament|direttiv|decision)\w*",
    re.IGNORECASE)
RE_ANAPH_ART = re.compile(
    r"\b(?:di\s+tale|di\s+dett[oa]|dell[oa]\s+stess[oa]|del(?:la)?\s+medesim[oa])\s+articolo\b",
    re.IGNORECASE)
RE_PRESENTE_AFTER = re.compile(
    r"^[^.;⟦▶]{0,45}\bpresente\s+(regolamento|direttiva)\b", re.IGNORECASE)


def resolve_year_num(a, b, has_n):
    a, b = int(a), int(b)
    if has_n:
        y, n = b, a
        if y < 100:
            y += 1900
        return (y, n) if 1950 <= y <= 2030 else (None, None)
    if 1950 <= a <= 2030:
        return a, b
    if 1950 <= b <= 2030:
        return b, a
    return None, None


def expected_act_key(word, year, num):
    """chiave attesa per (tipo testuale, anno, numero): corpus '13xx' o 'reg-YYYY-N'."""
    w = word.lower()
    base = "reg" if w.startswith("regolament") else ("dir" if w.startswith("direttiv") else "dec")
    if year == 2024 and str(num) in CORPUS_KEYS and base == ("dir" if str(num) == "1346" else "reg"):
        return {str(num)}
    # atti esterni: la chiave può avere varianti (dec, dec_impl, dec_framw…)
    return {f"{t}-{year}-{num}" for t in
            (base, base + "_impl", base + "_del", "dec_framw" if base == "dec" else base)}


def check_link(rec, ids, DATA, ext_files):
    problems = []
    d = rec["data"]
    text = rec["text"]
    href = rec["href"]
    page = rec["page"]
    is_ext = rec["ext"]

    # ---- ancora
    if not is_ext and not href.startswith("http"):
        if "#" in href:
            tpage, frag = href.split("#", 1)
            tpage = tpage or page
            if tpage not in ids:
                problems.append(f"pagina inesistente: {tpage}")
            elif frag not in ids[tpage]:
                problems.append(f"ancora inesistente: {href}")
        else:
            if href not in ids:
                problems.append(f"pagina inesistente: {href}")

    # ---- coerenza testo ↔ data-*
    m = RE_T_ART.search(text)
    if m:
        n, suff = m.group(1), (m.group(2) or "").lower()
        exp = n + (ORD_LETTER.get(suff, "") if suff else "")
        if d.get("art"):
            if d["art"] != exp and d["art"] != n:
                problems.append(f"testo 'articolo {n}{' ' + suff if suff else ''}' ma data-art={d['art']}")
        elif not is_ext and d.get("act") and not d.get("rct") and not d.get("anx") and not d.get("sec"):
            rec["flags"].append("ART_SENZA_ANCORA")  # link a pagina intera con testo 'articolo N'
    m = RE_T_PAR.search(text)
    if m:
        if d.get("par"):
            if d["par"] != m.group(1):
                problems.append(f"testo 'paragrafo {m.group(1)}' ma data-par={d['par']}")
        elif d.get("art"):
            rec["flags"].append("PAR_NON_ANCORATO")  # tooltip mostrerà l'articolo intero
    m = RE_T_BARE.match(text)
    if m and not is_ext:  # i link a TFUE/TUE (testo «78») sono verificati via CELEX
        n = m.group(1)
        if n not in (d.get("par"), d.get("art"), d.get("rct")) and not d.get("anx") and not d.get("sec"):
            # numero nudo deve essere art o par o considerando
            problems.append(f"testo '{n}' non corrisponde a art/par/cons ({d})")
    m = RE_T_ACT.search(text)
    if m and d.get("act"):
        year, num = resolve_year_num(m.group(3), m.group(4), bool(m.group(2).strip()))
        if year:
            exp = expected_act_key(m.group(1), year, num)
            if d["act"] not in exp:
                # refusi noti corretti a monte (2204/1348, 2019/1986, 2024/1436)
                known = {(2204, 1348): "1348", (2019, 1986): "reg-2019-1896", (2024, 1436): "1346"}
                if known.get((year, num)) != d["act"]:
                    problems.append(f"testo atto {year}/{num} ma data-act={d['act']}")
    if m and is_ext and "eur-lex" in href:
        year, num = resolve_year_num(m.group(3), m.group(4), bool(m.group(2).strip()))
        if year and f"/{year}/{num}/" not in href and f"/{year}/{num}?" not in href:
            problems.append(f"testo atto {year}/{num} ma href EUR-Lex {href}")
    m = RE_T_RCT.search(text)
    if m and d.get("rct") and d["rct"] != m.group(1):
        problems.append(f"testo 'considerando {m.group(1)}' ma data-rct={d['rct']}")
    m = RE_T_ANX.search(text)
    if m and d.get("anx") and d["anx"] != m.group(1).upper():
        problems.append(f"testo 'allegato {m.group(1)}' ma data-anx={d['anx']}")
    m = RE_T_SEC.search(text)
    if m and d.get("sec"):
        kind, roman = m.group(1).lower(), m.group(2).upper()
        if not d["sec"].endswith(f"_{kind}_{roman}"):
            problems.append(f"testo '{kind} {roman}' ma data-sec={d['sec']}")

    # ---- TFUE/TUE: numero articolo nel CELEX
    if is_ext and "CELEX:12016" in href:
        mn = re.search(r"(\d{1,3})\s*$", text) or RE_T_ART.search(text)
        mc = re.search(r"12016[EM](\d{3})", href)
        if mn and mc and int(mn.group(1)) != int(mc.group(1)):
            problems.append(f"articolo trattato {mn.group(1)} ma CELEX {mc.group(1)}")

    # ---- coerenza href ↔ data (ancora paragrafo)
    if not is_ext and "#" in href:
        frag = href.split("#", 1)[1]
        mp = re.match(r"^(\d{3})\.(\d{3})$", frag)
        if mp:
            if d.get("art") and int(mp.group(1)) != int(d["art"]):
                problems.append(f"ancora {frag} ma data-art={d['art']}")
            if d.get("par") and int(mp.group(2)) != int(d["par"]):
                problems.append(f"ancora {frag} ma data-par={d['par']}")
        mp = re.match(r"^art_(\d+[a-l]?)$", frag)
        if mp and d.get("art") and mp.group(1) != d["art"]:
            problems.append(f"ancora {frag} ma data-art={d['art']}")

    # ---- dati tooltip (hover deve mostrare testo inline)
    act = d.get("act")
    if act and not is_ext:
        src = DATA["acts"].get(act) or ext_files.get(act)
        if src is None:
            problems.append(f"data-act {act}: nessun dato tooltip (né data.js né data-ext)")
        else:
            if d.get("art"):
                a = src["articles"].get(d["art"])
                if not a:
                    problems.append(f"tooltip: articolo {d['art']} assente nei dati di {act}")
                elif not a.get("frags"):
                    problems.append(f"tooltip: articolo {d['art']} di {act} senza contenuto")
                elif d.get("par"):
                    pars = {f[0] for f in a["frags"]}
                    if int(d["par"]) not in pars:
                        rec["flags"].append("TIP_PAR_INTERO")  # mostrerà l'articolo intero
            elif d.get("rct"):
                if d["rct"] not in src.get("recitals", {}):
                    problems.append(f"tooltip: considerando {d['rct']} assente nei dati di {act}")
            else:
                pass  # link a pagina/atto intero: tooltip "Clic per aprire" + click = navigazione

    return problems


def simulate_tooltip(rec, DATA, ext_files):
    """Riproduce esattamente buildContent()/showTip() di app.js per stabilire
    cosa vede l'utente al passaggio del mouse / al clic. Ritorna (esito, dettaglio):
      art-par   : tooltip mostra il paragrafo citato evidenziato
      art-full  : tooltip mostra l'articolo intero (par non isolabile o assente nel testo)
      recital   : tooltip mostra il considerando
      act-note  : tooltip "Clic per aprire …" (link ad atto/pagina) — il clic naviga
      web       : link .ext a EUR-Lex: nessun tooltip, il clic apre in nuova scheda (cliccabile)
      VUOTO     : DIFETTO — buildContent restituirebbe null o corpo senza testo
    """
    d = rec["data"]
    href = rec["href"]
    if rec["ext"]:
        # app.js: i link .ext non attivano il tooltip; il click segue href (nuova scheda)
        return ("web", href if href.startswith("http") else "LINK NON HTTP")
    key = d.get("act")
    if not key:
        # nessun data-act: link interno semplice (capo/parte/allegato senza act?) → solo navigazione
        return ("act-note", "nessun data-act")
    src = DATA["acts"].get(key) or ext_files.get(key)
    if src is None:
        # buildContent ritorna null → showTip non mostra nulla; ma per gli atti esterni
        # app.js prova a caricarli da data-ext/<key>.js: se manca, tooltip resta "Caricamento…"
        return ("VUOTO", f"dati assenti per {key}")
    art = d.get("art")
    rct = d.get("rct")
    par = d.get("par")
    if rct:
        r = src.get("recitals", {}).get(rct)
        if not r or not str(r).strip():
            return ("VUOTO", f"considerando {rct} assente/vuoto in {key}")
        return ("recital", f"{key} cons. {rct}")
    if art:
        a = src["articles"].get(art)
        if not a:
            return ("VUOTO", f"articolo {art} assente in {key}")
        frags = a.get("frags") or []
        joined = "".join((f[1] or "") for f in frags)
        if not joined.strip():
            return ("VUOTO", f"articolo {art} di {key} senza testo")
        if par is not None:
            pars = {f[0] for f in frags}
            if int(par) in pars:
                return ("art-par", f"{key} art. {art} par. {par}")
            return ("art-full", f"{key} art. {art} (par. {par} non isolato → articolo intero)")
        return ("art-full", f"{key} art. {art}")
    # link ad atto/pagina intera: app.js mostra la nota "Clic per aprire …"
    note = ("Atto esterno al Patto — clic per aprire" if src.get("external")
            else "Clic per aprire il testo completo")
    return ("act-note", note)


def semantic_flags(rec, page_key, amend_arts):
    """classificazione per revisione semantica."""
    d = rec["data"]
    after = rec["after"]
    block = rec["block"]
    flags = rec["flags"]

    is_article_link = bool(d.get("art") or d.get("par"))
    if not is_article_link:
        return

    # anafora subito dopo il link (entro la stessa frase)
    m = RE_ANAPH.search(after[:95])
    if m and "." not in after[:m.start()]:
        flags.append("ANAFORA")

    # anafora d'articolo («di detto articolo») nella stessa frase dopo il link
    m = RE_ANAPH_ART.search(after[:110])
    if m and "." not in after[:m.start()]:
        flags.append("ANAFORA_ART")

    # "del presente regolamento" dopo il link ma target esterno
    if RE_PRESENTE_AFTER.search(after) and d.get("act") != page_key:
        flags.append("PRESENTE_MA_CROSS")

    # link interno senza atto esplicito nel testo, con altro atto citato prima nel blocco
    if d.get("act") == page_key:
        pre = rec["before"]
        others = set(re.findall(r"⟦[^⟧‖]*‖((?:reg|dir|dec)[^:⟧]*|13\d\d)", pre))
        others |= set(re.findall(r"▶[^◀‖]*‖((?:reg|dir|dec)[^:◀]*)", pre))
        others.discard(page_key)
        if others and "presente" not in after[:60].lower():
            flags.append("ALTRO_ATTO_PRIMA")

    # link dentro testo virgolettato «…» (testo destinato a un altro atto)
    opens = rec["before"].count("«") - rec["before"].count("»")
    if opens > 0 or rec["quote"]:
        flags.append("IN_VIRGOLETTATO")

    # link interno dentro un articolo di modifica (i rinvii nudi lì sono dell'atto modificato)
    if rec["scope"] in amend_arts and d.get("act") == page_key:
        flags.append("IN_ART_MODIFICA")

    # cross-act senza menzione esplicita dell'atto bersaglio nel blocco
    if d.get("act") != page_key and d.get("act") and not rec["ext"]:
        tgt = d["act"]
        mentioned = (f"‖{tgt}⟧" in block or f"‖{tgt}:" in block or f"‖{tgt}◀" in block)
        if not mentioned and not RE_ANAPH.search(block) and not RE_ANAPH_ART.search(block):
            flags.append("CROSS_SENZA_MENZIONE")

    # paragrafo standalone → articolo contenitore, ma un ALTRO articolo è citato
    # prima nella stessa frase (l'antecedente potrebbe essere quello)
    if (d.get("act") == page_key and d.get("art") and rec["scope"] == f"art_{d['art']}"
            and RE_T_BARE.match(rec["text"])):
        pre = rec["before"]
        last_art_m = None
        for mm in re.finditer(r"⟦[^⟧‖]*articolo[^⟧‖]*‖" + re.escape(page_key) + r":art(\d+)", pre):
            last_art_m = mm
        if last_art_m and last_art_m.group(1) != d["art"]:
            between = pre[last_art_m.end():]
            if "." not in between and ";" not in between:
                flags.append("PAR_DOPO_ALTRO_ART")


# ---------------------------------------------------------------- main

def main():
    print("Carico dati tooltip…")
    DATA, ext_files = load_pacto_data()
    print(f"  data.js: {len(DATA['acts'])} atti; data-ext: {len(ext_files)} file")

    print("Indicizzo id di tutte le pagine…")
    ids = collect_ids()
    print(f"  {len(ids)} pagine")

    all_recs = []
    seq = 0
    for key in CORPUS_KEYS:
        fp = SITE / f"{key}.html"
        soup = BeautifulSoup(fp.read_text(encoding="utf-8"), "lxml")
        # articoli "di modifica" (rubrica che inizia con Modifi… o testo «così modificat»)
        amend_arts = set()
        for div in soup.find_all("div", class_="eli-subdivision", id=re.compile(r"^art_\d+$")):
            sti = div.find("p", class_="oj-sti-art")
            head = sti.get_text(" ", strip=True).lower() if sti else ""
            if head.startswith("modifi") or "così modificat" in div.get_text(" ", strip=True).lower():
                amend_arts.add(div["id"])
        links = soup.find_all("a", class_="xref")
        print(f"  {key}: {len(links)} link")
        for a in links:
            seq += 1
            art, par_div, rct, anx, quote = scope_of(a)
            block = find_block(a)
            annotated = annotate_block(block, a)
            # blocco precedente (per risolvere anafore che scavalcano il paragrafo)
            prev = block.find_previous(("p", "td"))
            prev_text = ""
            if prev is not None:
                prev_text = re.sub(r"\s+", " ", annotate_block(prev, a))[-450:]
            # posizione del link corrente nell'annotazione
            mcur = re.search(r"▶([^◀]*)◀", annotated)
            before = annotated[:mcur.start()][-420:] if mcur else ""
            after = annotated[mcur.end():][:420] if mcur else ""
            d = {k.replace("data-", ""): v for k, v in a.attrs.items() if k.startswith("data-")}
            rec = dict(
                id=seq, page=f"{key}.html", act=key,
                scope=art or rct or anx or "", par_div=par_div, quote=quote,
                text=norm(a.get_text()), href=a.get("href", ""),
                ext="ext" in (a.get("class") or []),
                data=d, before=before, after=after,
                block=annotated[:1700], prev_block=prev_text, flags=[], problems=[],
            )
            rec["problems"] = check_link(rec, ids, DATA, ext_files)
            semantic_flags(rec, key, amend_arts)
            tip_kind, tip_det = simulate_tooltip(rec, DATA, ext_files)
            rec["tip"] = tip_kind
            rec["tip_det"] = tip_det
            if tip_kind == "VUOTO":
                rec["problems"].append(f"TOOLTIP VUOTO: {tip_det}")
            all_recs.append(rec)

    # ---- output
    with open(OUTDIR / "links_all.jsonl", "w", encoding="utf-8") as f:
        for r in all_recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    problems = [r for r in all_recs if r["problems"]]
    with open(OUTDIR / "problems.json", "w", encoding="utf-8") as f:
        json.dump(problems, f, ensure_ascii=False, indent=1)

    SEM_FLAGS = {"ANAFORA", "ANAFORA_ART", "PRESENTE_MA_CROSS", "ALTRO_ATTO_PRIMA",
                 "IN_VIRGOLETTATO", "IN_ART_MODIFICA", "CROSS_SENZA_MENZIONE",
                 "PAR_DOPO_ALTRO_ART"}
    suspects = [r for r in all_recs if SEM_FLAGS & set(r["flags"])]
    with open(OUTDIR / "suspects.jsonl", "w", encoding="utf-8") as f:
        for r in suspects:
            slim = {k: r[k] for k in ("id", "page", "scope", "par_div", "quote", "text",
                                      "href", "data", "block", "prev_block", "flags")}
            f.write(json.dumps(slim, ensure_ascii=False) + "\n")

    degraded = [r for r in all_recs
                if {"TIP_PAR_INTERO", "ART_SENZA_ANCORA", "PAR_NON_ANCORATO"} & set(r["flags"])]
    with open(OUTDIR / "degraded.jsonl", "w", encoding="utf-8") as f:
        for r in degraded:
            slim = {k: r[k] for k in ("id", "page", "scope", "par_div", "text", "href",
                                      "data", "flags")}
            f.write(json.dumps(slim, ensure_ascii=False) + "\n")

    cnt = Counter()
    for r in all_recs:
        for fl in r["flags"]:
            cnt[fl] += 1
    by_page_problems = Counter(r["page"] for r in problems)

    lines = []
    lines.append(f"Link totali: {len(all_recs)}")
    lines.append(f"Link con problemi deterministici: {len(problems)} {dict(by_page_problems)}")
    lines.append(f"Link da revisione semantica: {len(suspects)}")
    lines.append("Flag: " + json.dumps(cnt, ensure_ascii=False, indent=0))
    kinds = Counter()
    for r in all_recs:
        d = r["data"]
        if r["ext"]:
            kinds["esterno-web"] += 1
        elif d.get("rct"):
            kinds["considerando"] += 1
        elif d.get("anx"):
            kinds["allegato"] += 1
        elif d.get("sec"):
            kinds["capo/parte"] += 1
        elif d.get("art") and d.get("act") in CORPUS_KEYS:
            kinds["articolo-corpus"] += 1
        elif d.get("art"):
            kinds["articolo-ext-locale"] += 1
        elif d.get("act") in CORPUS_KEYS:
            kinds["atto-corpus"] += 1
        else:
            kinds["atto-ext-locale"] += 1
    lines.append("Tipi: " + json.dumps(kinds, ensure_ascii=False, indent=0))

    # ---- salute dei tooltip (requisito #2: ogni hover mostra testo inline)
    tip_cnt = Counter(r["tip"] for r in all_recs)
    empty = [r for r in all_recs if r["tip"] == "VUOTO"]
    lines.append("")
    lines.append("Tooltip (cosa vede l'utente al passaggio del mouse / clic):")
    lines.append(f"  art-par   {tip_cnt.get('art-par',0):5d}  mostra il paragrafo citato evidenziato")
    lines.append(f"  art-full  {tip_cnt.get('art-full',0):5d}  mostra l'articolo intero inline")
    lines.append(f"  recital   {tip_cnt.get('recital',0):5d}  mostra il considerando inline")
    lines.append(f"  act-note  {tip_cnt.get('act-note',0):5d}  nota «Clic per aprire» + clic naviga all'atto")
    lines.append(f"  web       {tip_cnt.get('web',0):5d}  link EUR-Lex: clic apre in nuova scheda")
    lines.append(f"  VUOTO     {len(empty):5d}  DIFETTO: tooltip senza testo")
    # i link "act-note" con testo «articolo N» mostrano la nota generica invece dell'articolo:
    # inline non disponibile perché l'articolo non è nei dati (atto esterno non consolidato)
    art_text_note = [r for r in all_recs if r["tip"] == "act-note"
                     and RE_T_ART.search(r["text"])]
    lines.append(f"  ↳ di cui «articolo N» senza testo inline (atto esterno non consolidato): {len(art_text_note)}")
    with open(OUTDIR / "tooltip_no_inline.jsonl", "w", encoding="utf-8") as f:
        for r in art_text_note:
            f.write(json.dumps({k: r[k] for k in ("id","page","scope","text","href","data","tip_det")},
                               ensure_ascii=False) + "\n")

    summary = "\n".join(lines)
    (OUTDIR / "summary.txt").write_text(summary + "\n", encoding="utf-8")
    print(summary)

    if empty:
        print("\nTOOLTIP VUOTI (da risolvere):")
        for r in empty[:30]:
            print(f"  [{r['page']} {r['scope']}] '{r['text']}' → {r['tip_det']}")
    if problems:
        print("\nPrimi problemi deterministici:")
        for r in problems[:15]:
            print(f"  [{r['page']} {r['scope']}] '{r['text']}' → {r['href']}: {r['problems']}")


if __name__ == "__main__":
    main()
