# -*- coding: utf-8 -*-
"""
Genera il sito statico "Patto interattivo": versioni navigabili dei 10 atti
del Patto UE migrazione e asilo, con ogni riferimento normativo trasformato
in link + anteprima al passaggio del mouse.

Fonte: file HTML EUR-Lex (formato ELI/CONVEX) in "TEsti html/".
Output: cartella "Patto interattivo/" (pagine, assets, audit.html).
"""

import json
import re
import sys
import unicodedata
from pathlib import Path
from collections import defaultdict

from bs4 import BeautifulSoup, NavigableString, Tag

BASE = Path(__file__).parent
SRC = BASE / "TEsti html"
OUT = BASE / "Patto interattivo"

ACTS = [
    dict(key="1346", typ="dir", year=2024, num=1346, src="1346 dir accoglienza.html",
         short="Direttiva accoglienza", word="direttiva",
         title="Direttiva accoglienza", nav="Accoglienza"),
    dict(key="1347", typ="reg", year=2024, num=1347, src="1347 Qualifiche.html",
         short="Reg. qualifiche", word="regolamento",
         title="Regolamento qualifiche", nav="Qualifiche"),
    dict(key="1348", typ="reg", year=2024, num=1348, src="1348 procedure.html",
         short="Reg. procedure", word="regolamento",
         title="Regolamento procedure", nav="Procedure"),
    dict(key="1349", typ="reg", year=2024, num=1349, src="1349 rimpatrio frontiera.html",
         short="Reg. rimpatrio frontiera", word="regolamento",
         title="Regolamento rimpatrio alla frontiera", nav="Rimpatrio"),
    dict(key="1350", typ="reg", year=2024, num=1350, src="1350 riammissione.html",
         short="Reg. reinsediamento", word="regolamento",
         title="Regolamento reinsediamento e ammissione umanitaria", nav="Reinsediamento"),
    dict(key="1351", typ="reg", year=2024, num=1351, src="1351 RAMM.html",
         short="Reg. RAMM (Dublino)", word="regolamento",
         title="Regolamento gestione asilo e migrazione (RAMM)", nav="RAMM"),
    dict(key="1352", typ="reg", year=2024, num=1352, src="1352 — Modifiche ECRIS-TCN.html",
         short="Reg. modifiche ECRIS-TCN", word="regolamento",
         title="Regolamento modifiche ECRIS-TCN", nav="ECRIS"),
    dict(key="1356", typ="reg", year=2024, num=1356, src="1356 screening.html",
         short="Reg. screening", word="regolamento",
         title="Regolamento screening", nav="Screening"),
    dict(key="1358", typ="reg", year=2024, num=1358, src="1358 — Eurodac.html",
         short="Reg. Eurodac", word="regolamento",
         title="Regolamento Eurodac", nav="Eurodac"),
    dict(key="1359", typ="reg", year=2024, num=1359, src="1359 — Crisi e forza maggiore.html",
         short="Reg. crisi e forza maggiore", word="regolamento",
         title="Regolamento crisi e forza maggiore", nav="Crisi"),
]

CORPUS = {("reg" if a["typ"] == "reg" else "dir", a["year"], a["num"]): a["key"] for a in ACTS}

# atti esterni scaricati da CELLAR (vedi scarica_atti_esterni.py)
EXT_SRC = BASE / "Atti esterni html"
EXT = {}          # (t, year, num) -> ext act dict
EXT_BY_KEY = {}   # "reg-2013-604" -> ext act dict

ORD_LETTER = {"bis": "a", "ter": "b", "quater": "c", "quinquies": "d", "sexies": "e",
              "septies": "f", "octies": "g", "novies": "h", "nonies": "h",
              "decies": "i", "undecies": "j", "duodecies": "k", "terdecies": "l"}
EXT_TNAME = {"reg": "Regolamento", "reg_impl": "Regolamento di esecuzione",
             "reg_del": "Regolamento delegato", "dir": "Direttiva",
             "dir_impl": "Direttiva di esecuzione", "dir_del": "Direttiva delegata",
             "dec": "Decisione", "dec_impl": "Decisione di esecuzione",
             "dec_framw": "Decisione quadro"}
EXT_SHORT = {"reg": "Reg.", "reg_impl": "Reg. esec.", "reg_del": "Reg. del.",
             "dir": "Dir.", "dir_impl": "Dir. esec.", "dir_del": "Dir. del.",
             "dec": "Dec.", "dec_impl": "Dec. esec.", "dec_framw": "Dec. quadro"}

NBSP = " "
SP = r"[\s]+"  # python \s già include NBSP in modalità unicode

EXCLUDED_CLASSES = {
    "oj-doc-ti", "oj-ti-art", "oj-sti-art", "oj-ti-section-1", "oj-ti-section-2",
    "oj-ti-anx", "oj-sti-anx", "oj-hd-ti", "oj-hd-lg", "oj-hd-coll", "oj-hd-uniq",
    "oj-hd-date", "oj-final",
}

ORDINALS = (r"(?:bis|ter|quater|quinquies|sexies|septies|octies|novies|nonies|"
            r"decies|undecies|duodecies|terdecies)")

RE_ART = re.compile(r"articol([oi])" + SP + r"(?=\d|da\s)", re.IGNORECASE)
RE_NUM = re.compile(r"(\d{1,3})((?:[\s-]" + ORDINALS + r")?)\b")
RE_LIST_SEP = re.compile(r"(?:\s*,\s*|\s+(?:e|o|od)\s+)(?=\d)")
RE_LIST_SEP_X = re.compile(r"(?:\s*,\s*|\s+(?:e|ed|o|od)\s+)(?=\d|da\s+\d)")
RE_RANGE = re.compile(r"da" + SP + r"(\d{1,3})" + SP + r"a" + SP + r"(\d{1,3})\b")
RE_CHAIN = re.compile(
    r"\s*[,;]?\s*(?:e|ed|o|od|nonché)?\s*(?:di" + SP + r"cui" + SP + r")?"
    r"(?:l['’]|all['’]|dell['’]|dall['’]|sull['’]|agli|degli|negli|gli)?\s*(?=articol[oi][\s])",
    re.IGNORECASE)

RE_PAR_Q = re.compile(r"\s*,?\s*paragraf([oi])" + SP + r"(?=\d)")
# una "lettera" è quasi sempre «a)», «a bis)»; la forma nuda («lettera b,» — refuso GU)
# è ammessa solo se non è una parola funzione, altrimenti il consumo di qualificatori
# mangerebbe «di», «e», «al»… rompendo il riconoscimento delle code («di tale regolamento»)
LETT_STOP = r"(?:e|ed|o|od|a|ai|al|di|da|de|del|in|su|si|se|la|le|lo|il|un|ne|tra|fra|per|che|chi|cui|non)"
LETT = (r"(?:[a-z]{1,2}(?:[\s-]" + ORDINALS + r")?\)"
        r"|(?!" + LETT_STOP + r"\b)[a-z]{1,2}\b)")
RE_LETT_Q = re.compile(
    r"\s*,?\s*letter[ae]" + SP + r"(?:da" + SP + r")?" + LETT +
    r"(?:" + SP + r"a" + SP + LETT + r")?"
    r"(?:(?:\s*,\s*|\s+(?:e|ed|o|od)\s+)(?:da" + SP + r")?" + LETT +
    r"(?:" + SP + r"a" + SP + LETT + r")?)*",
    re.IGNORECASE)
RE_PUNTO_Q = re.compile(
    r"\s*,?\s*punt[oi]" + SP + r"(?:da" + SP + r")?\d{1,3}\)?(?:" + SP + r"a" + SP + r"\d{1,3}\)?)?"
    r"(?:(?:\s*,\s*|\s+(?:e|ed|o|od)\s+)(?:da" + SP + r")?\d{1,3}\)?(?:" + SP + r"a" + SP + r"\d{1,3}\)?)?)*",
    re.IGNORECASE)
# continuazione di paragrafi dopo i qualificatori: «…, lettera f), e paragrafo 5, lettera b)»
RE_PAR_CONT = re.compile(
    r"\s*,?\s*(?:e|ed|o|od|nonché)\s+(?:il\s+|al\s+|nel\s+|all['’]\s*)?paragraf[oi]" + SP + r"(?=\d)",
    re.IGNORECASE)
RE_COMMA_Q = re.compile(
    r"\s*,?\s*(?:primo|secondo|terzo|quarto|quinto|sesto|settimo|ottavo|ultimo)" + SP + r"comma",
    re.IGNORECASE)
RE_FRASE_Q = re.compile(
    r"\s*,?\s*(?:prima|seconda|terza|ultima)" + SP + r"frase", re.IGNORECASE)

RE_PRESENTE = re.compile(
    r"\s*,?\s*(?:del|della)" + SP + r"presente" + SP + r"(regolamento|direttiva)\b",
    re.IGNORECASE)
RE_TFUE = re.compile(r"\s*,?\s*(?:del" + SP + r")?(TFUE|TUE)\b")
RE_TRATTATO_F = re.compile(
    r"\s*,?\s*del" + SP + r"trattato" + SP + r"sul" + SP + r"funzionamento" + SP +
    r"dell['’]Unione(?:" + SP + r"europea)?", re.IGNORECASE)
RE_TRATTATO_U = re.compile(
    r"\s*,?\s*del" + SP + r"trattato" + SP + r"sull['’]Unione" + SP + r"europea", re.IGNORECASE)
RE_CARTA = re.compile(r"\s*,?\s*della" + SP + r"Carta\b(?!" + SP + r"delle)")
RE_REG_FIN = re.compile(r"\s*,?\s*del" + SP + r"regolamento" + SP + r"finanziario\b", re.IGNORECASE)
RE_SKIP_TAIL = re.compile(
    r"\s*,?\s*(?:del|della|dell['’]|dello|di" + SP + r"tal[ei]|di" + SP + r"dett[oa])" + SP +
    r"(?:protocoll|convenzion|accord|statut|trattato" + SP + r"di|Carta" + SP + r"delle)",
    re.IGNORECASE)
RE_STESSO = re.compile(
    r"\s*,?\s*(?:dell[oa]" + SP + r"stess[oa]|di" + SP + r"tal[ei]|di" + SP + r"dett[oa]|"
    r"del(?:la)?" + SP + r"medesim[oa])" + SP + r"(?:regolament|direttiv|decision)\w*",
    re.IGNORECASE)
# «di detto articolo», «dello stesso articolo», «del medesimo articolo»: anafora
# all'ultimo articolo citato (last_art), non all'articolo che contiene il testo
RE_STESSO_ART = re.compile(
    r"\s*,?\s*(?:di" + SP + r"(?:tale|dett[oa])|dell[oa]" + SP + r"stess[oa]|"
    r"del(?:la)?" + SP + r"medesim[oa])" + SP + r"articolo\b",
    re.IGNORECASE)
# catena di gruppi-paragrafo: «al paragrafo 7, lettera a), o al paragrafo 7, lettera b), di…»
RE_PAR_CHAIN = re.compile(
    r"\s*[,;]?\s*(?:e|ed|o|od|nonché)?\s*(?:al|all['’])?\s*(?=paragraf[oi][\s])",
    re.IGNORECASE)

RE_ACT = re.compile(
    r"(regolament[oi]|direttiv[ae]|decision[ei])"
    r"((?:" + SP + r"(?:di" + SP + r"esecuzione|delegat[oa]|quadro))?)"
    r"(?:" + SP + r"\((UE,?\s*Euratom|UE|CE|CEE|EU)\))?"
    r"(?:" + SP + r"|\s*)"
    r"((?:n\.\s*)?)"
    r"(\d{1,4})/(\d{1,4})"
    r"((?:/(?:CE|CEE|UE|GAI|PESC|Euratom))?)",
    re.IGNORECASE)

RE_ACT_TAIL = re.compile(
    r"\s*,?\s*(?:del|della|dell['’]|di" + SP + r"cui" + SP + r"al(?:la)?)" + SP +
    r"(?=(?:regolament|direttiv|decision))", re.IGNORECASE)

RE_CONSIDERANDO = re.compile(r"considerando" + SP + r"(?=\d)", re.IGNORECASE)
RE_ALLEGATO = re.compile(r"allegat([oi])" + SP + r"(?=[IVX]+\b|\d)", re.IGNORECASE)
RE_PARAGRAFO_STANDALONE = re.compile(r"paragraf([oi])" + SP + r"(?=\d)", re.IGNORECASE)
RE_DELL_ARTICOLO = re.compile(
    r"\s*,?\s*(?:del(?:l['’])?|di" + SP + r"cui" + SP + r"al(?:l['’])?)" + SP + r"?articolo" + SP, re.IGNORECASE)
RE_PRES_ART = re.compile(r"\s*,?\s*del" + SP + r"presente" + SP + r"articolo\b", re.IGNORECASE)
RE_PARTE = re.compile(r"\bparte" + SP + r"([IVX]+)\b")
RE_CAPO = re.compile(r"\bcapo" + SP + r"([IVX]+)\b")
RE_DELLA_PARTE = re.compile(r"\s*,?\s*della" + SP + r"parte" + SP + r"([IVX]+)\b", re.IGNORECASE)
RE_PRES_PARTE = re.compile(r"\s*,?\s*della" + SP + r"presente" + SP + r"parte\b", re.IGNORECASE)
RE_ROMAN = re.compile(r"^[IVX]+$")


def norm(s):
    return unicodedata.normalize("NFC", s)


def eli_type(word, variant):
    w = word.lower()
    v = re.sub(r"\s+", " ", variant.lower()).strip()
    base = {"r": "reg", "d_dir": "dir", "d_dec": "dec"}
    if w.startswith("regolament"):
        t = "reg"
    elif w.startswith("direttiv"):
        t = "dir"
    else:
        t = "dec"
    if "esecuzione" in v:
        t += "_impl"
    elif "delegat" in v:
        t += "_del"
    elif "quadro" in v:
        t = "dec_framw"
    return t


def resolve_year_num(a, b, has_n=False):
    """«n. 604/2013» = numero/anno (stile vecchio); «2024/1348» = anno/numero."""
    a, b = int(a), int(b)
    if has_n:
        year, num = b, a
        if year < 100:
            year += 1900
        return (year, num) if 1950 <= year <= 2030 else (None, None)
    year, num = a, b
    if year < 100:
        year += 1900
    if 1950 <= year <= 2030:
        return year, num
    if 1950 <= b <= 2030:
        return b, a
    return None, None


class Audit:
    def __init__(self):
        self.counts = defaultdict(lambda: defaultdict(int))
        self.issues = []

    def count(self, act, kind, n=1):
        self.counts[act][kind] += n

    def issue(self, act, reason, snippet):
        snippet = re.sub(r"\s+", " ", snippet).strip()
        self.issues.append((act, reason, snippet))


AUDIT = Audit()


# ---------------------------------------------------------------- estrazione

def load_act(act):
    html = (SRC / act["src"]).read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "lxml")
    containers = soup.find_all("div", class_="eli-container")
    if not containers:
        sys.exit(f"eli-container non trovato in {act['src']}")
    container = containers[0]
    # gli allegati sono eli-container separati con id "anx_ I" (con NBSP)
    anx_els = []
    for c in containers[1:]:
        cid = c.get("id", "")
        if cid.lower().startswith("anx"):
            c["id"] = "anx_" + re.sub(r"[\s_]+", "", cid[3:]).upper()
            anx_els.append(c)
    act["anx_els"] = anx_els

    title_el = container.find(class_="oj-doc-ti")
    title_parts = [norm(p.get_text(" ", strip=True))
                   for p in container.select(".eli-main-title p.oj-doc-ti")]
    act["full_title"] = " ".join(title_parts) if title_parts else norm(title_el.get_text(" ", strip=True))

    arts = {}
    for div in container.find_all("div", class_="eli-subdivision"):
        did = div.get("id", "")
        m = re.match(r"^art_(\d+)$", did)
        if not m:
            continue
        n = int(m.group(1))
        lab = div.find("p", class_="oj-ti-art")
        sti = div.find("p", class_="oj-sti-art")
        arts[n] = dict(
            id=did,
            label=norm(lab.get_text(" ", strip=True)) if lab else f"Articolo {n}",
            heading=norm(sti.get_text(" ", strip=True)) if sti else "",
            el=div,
        )

    pars = {}
    for div in container.find_all("div", id=re.compile(r"^\d+\.\d+$")):
        a, p = div["id"].split(".")
        pars[(int(a), int(p))] = div["id"]

    rcts = {}
    for div in container.find_all("div", class_="eli-subdivision", id=re.compile(r"^rct_\d+$")):
        rcts[int(div["id"][4:])] = div["id"]

    anxs = {}
    for el in anx_els:
        label_el = el.find(class_="oj-doc-ti")
        text = norm((label_el or el).get_text(" ", strip=True))[:60]
        m = re.search(r"ALLEGATO\s+([IVX]+|\d+)", text, re.IGNORECASE)
        roman = m.group(1).upper() if m else el["id"].replace("anx_", "").strip().upper() or "I"
        anxs.setdefault(roman, el["id"])

    # parti / capi: i titoli di sezione non hanno id → li generiamo
    sections = []
    cur_part = None
    pending = None
    seq = 0
    for p in container.find_all("p", class_="oj-ti-section-1"):
        text = norm(p.get_text(" ", strip=True))
        m = re.match(r"(PARTE|CAPO|SEZIONE)\s+([IVX]+|\d+)", text, re.IGNORECASE)
        if not m:
            continue
        kind = m.group(1).upper()
        roman = m.group(2).upper()
        seq += 1
        sid = f"sec_{seq}_{kind.lower()}_{roman}"
        p["id"] = sid
        if kind == "PARTE":
            cur_part = roman
        sections.append(dict(kind=kind, roman=roman, part=cur_part if kind != "PARTE" else None,
                             id=sid, title=text))

    # articoli «di modifica»: i riferimenti senza coda esplicita appartengono
    # all'atto modificato, non a questo
    amend_ids = set()
    for n, info in arts.items():
        head = (info["heading"] or "").lower()
        if head.startswith("modifi"):
            amend_ids.add(info["id"])
            continue
        body = info["el"].get_text(" ", strip=True).lower()
        if "così modificat" in body:
            amend_ids.add(info["id"])

    act.update(soup=soup, container=container, arts=arts, pars=pars,
               rcts=rcts, anxs=anxs, sections=sections, amend_ids=amend_ids)
    return act


# ------------------------------------------------------- atti esterni (CELLAR)

RE_ART_TITLE = re.compile(r"^Articolo\s+(\d+)\s*(" + ORDINALS + r")?\s*$", re.IGNORECASE)
RE_STOP_CLASS = re.compile(r"^(title-division|title-annex|doc-ti|title-doc|annex)")


def segment_consleg(soup, existing=()):
    """Articoli con titolo <p class='title-article-norm'> ma senza contenitore art_N:
    assegna id art_X ai titoli e raccoglie i blocchi fino al titolo successivo.
    `existing` = chiavi già estratte via eli-subdivision (saltate)."""
    titles = soup.find_all("p", class_="title-article-norm")
    parsed = []
    for t in titles:
        m = RE_ART_TITLE.match(norm(t.get_text(" ", strip=True)))
        if not m:
            continue
        artkey = ext_artkey(int(m.group(1)), m.group(2))
        parsed.append((artkey, t))
    title_set = {id(t) for _, t in parsed}
    arts = {}
    for artkey, t in parsed:
        if artkey in arts or artkey in existing:
            continue
        if any(True for p in t.parents
               if isinstance(p, Tag) and re.match(r"^art_", p.get("id", ""))):
            continue  # titolo dentro un articolo già estratto via eli-subdivision
        t["id"] = f"art_{artkey}"
        heading = ""
        frags = []
        collected = set()
        for el in t.next_elements:
            if not isinstance(el, Tag):
                continue
            if id(el) in title_set:
                break
            classes = el.get("class") or []
            if any(RE_STOP_CLASS.match(c) for c in classes):
                break
            if el.name not in ("p", "div", "table"):
                continue
            if any(id(parent) in collected for parent in el.parents):
                continue
            collected.add(id(el))
            if "stitle-article-norm" in classes:
                if not heading:
                    heading = norm(el.get_text(" ", strip=True))
                continue
            frags.append([None, clean_copy_html(el)])
        base = artkey.rstrip("abcdefghi")
        sfx = artkey[len(base):]
        label = f"Articolo {base}"
        if sfx:
            inv = {v: k for k, v in ORD_LETTER.items()}
            label += f" {inv.get(sfx, sfx)}"
        arts[artkey] = dict(anchor=f"art_{artkey}", label=label, heading=heading,
                            el=None, frags_pre=frags)
    return arts


def load_ext_acts():
    """Carica e indicizza gli atti esterni scaricati. Popola EXT / EXT_BY_KEY."""
    mpath = EXT_SRC / "manifest.json"
    if not mpath.exists():
        return
    manifest = json.load(open(mpath, encoding="utf-8"))
    for key, meta in manifest.items():
        if not meta.get("version"):
            continue
        fp = EXT_SRC / f"{key}.html"
        if not fp.exists():
            continue
        soup = BeautifulSoup(fp.read_text(encoding="utf-8"), "lxml")
        # pulizia: via script/style/link/img, e tutti i <a> diventano testo
        for tag in soup.find_all(["script", "style", "link", "meta", "img"]):
            tag.decompose()
        for a in soup.find_all("a"):
            a.unwrap()
        containers = soup.find_all("div", class_="eli-container") or [soup.body or soup]

        arts = {}
        for div in soup.find_all("div", class_="eli-subdivision",
                                 id=re.compile(r"^art_\d+[a-z]?$")):
            artkey = div["id"][4:]
            lab = div.find("p", class_=re.compile(r"^(oj-)?ti-art$|^title-article-norm$"))
            sti = div.find("p", class_=re.compile(r"^(oj-)?sti-art$|^stitle-article-norm$"))
            arts[artkey] = dict(
                anchor=div["id"],
                label=norm(lab.get_text(" ", strip=True)) if lab else f"Articolo {artkey}",
                heading=norm(sti.get_text(" ", strip=True)) if sti else "",
                el=div)
        # integrazione: articoli inseriti dai consolidamenti senza contenitore proprio
        extra = segment_consleg(soup, existing=set(arts))
        arts.update(extra)
        if not arts:
            continue
        if extra:  # riordina in ordine di documento (per il sommario)
            order = [el["id"][4:] for el in soup.find_all(id=re.compile(r"^art_\d+[a-z]?$"))]
            arts = {k: arts[k] for k in order if k in arts}
        title_el = soup.find("p", class_=re.compile(r"^(oj-doc-ti|title-doc-first)$"))
        full = norm(title_el.get_text(" ", strip=True)) if title_el else key
        t, year, num = meta["t"], meta["year"], meta["num"]
        ext = dict(key=key, t=t, year=year, num=num, page=f"ext-{key}.html",
                   short=f"{EXT_SHORT[t]} {num}/{year}" if year < 2015
                         else f"{EXT_SHORT[t]} {year}/{num}",
                   label=full[:160], version=meta["version"],
                   eurlex=eurlex_url(t, year, num),
                   cites=meta.get("cites", 0),
                   arts=arts, containers=containers, soup=soup)
        EXT[(t, year, num)] = ext
        EXT_BY_KEY[key] = ext


def ext_artkey(num, suffix):
    """'7', 'bis' -> '7a' (convenzione CONVEX)."""
    if suffix:
        letter = ORD_LETTER.get(suffix.lower())
        if not letter:
            return None
        return f"{num}{letter}"
    return str(num)


# ---------------------------------------------------------------- targeting

def page_for(key):
    return f"{key}.html"


def art_href(reg, target_key, art, par):
    """href + esistenza per un riferimento ad articolo del corpus."""
    t = reg[target_key]
    if art not in t["arts"]:
        return None, None
    anchor = t["arts"][art]["id"]
    if par is not None and (art, par) in t["pars"]:
        anchor = t["pars"][(art, par)]
    elif par is not None:
        par = None  # paragrafo senza ancora → ripiega sull'articolo
    return f"{page_for(target_key)}#{anchor}", par


def eurlex_url(t, year, num):
    return f"https://eur-lex.europa.eu/eli/{t}/{year}/{num}/oj/ita"


TFUE_URL = "https://eur-lex.europa.eu/legal-content/IT/TXT/?uri=CELEX:12016E{art:03d}"
TUE_URL = "https://eur-lex.europa.eu/legal-content/IT/TXT/?uri=CELEX:12016M{art:03d}"
CARTA_URL = "https://eur-lex.europa.eu/legal-content/IT/TXT/?uri=CELEX:12012P/TXT"


# ---------------------------------------------------------------- parser

class Emit:
    """un link da inserire: [start,end) nel testo, href, attributi data."""
    def __init__(self, start, end, href, cls="xref", **data):
        self.start, self.end, self.href, self.cls, self.data = start, end, href, cls, data


def parse_act_ref(text, pos):
    """Prova a leggere un riferimento ad atto a partire da pos.
    Ritorna (end, match_info) o (None, None)."""
    m = RE_ACT.match(text, pos)
    if not m:
        return None, None
    word, variant, paren, n_marker, n1, n2, suffix = m.groups()
    if not paren and not suffix and not n_marker.strip():
        # senza (UE)/(CE), senza /CE finale e senza "n." è troppo ambiguo
        return None, None
    year, num = resolve_year_num(n1, n2, has_n=bool(n_marker.strip()))
    if year is None:
        return None, None
    t = eli_type(word, variant or "")
    return m.end(), dict(word=word, t=t, year=year, num=num, span=(m.start(), m.end()))


RE_ACT_CONT = re.compile(
    r"(?:\s*,\s*(?:e|ed|o|od)?\s*|\s+(?:e|ed|o|od)\s+)(?:se" + SP + r"del" + SP + r"caso\s*,?\s*)?"
    r"(?:\((UE,?\s*Euratom|UE|CE|CEE|EU)\)\s*)?"
    r"((?:n\.\s*)?)"
    r"(\d{1,4})/(\d{1,4})"
    r"((?:/(?:CE|CEE|UE|GAI|PESC|Euratom))?)",
    re.IGNORECASE)


def parse_act_refs(text, pos):
    """Un riferimento ad atto, eventualmente in elenco:
    «regolamenti (UE) 2019/817 e (UE) 2019/818», «direttive 2002/90/CE e 2008/115/CE».
    Ritorna (end, [info, ...]) o (None, None)."""
    end, info = parse_act_ref(text, pos)
    if not info:
        return None, None
    infos = [info]
    while True:
        m = RE_ACT_CONT.match(text, end)
        if not m:
            break
        paren, n_marker, n1, n2, suffix = m.groups()
        if not paren and not suffix and not n_marker.strip():
            break
        year, num = resolve_year_num(n1, n2, has_n=bool(n_marker.strip()))
        if year is None:
            break
        if paren:
            s0 = m.start(1) - 1  # parentesi aperta
        elif n_marker.strip():
            s0 = m.start(2)
        else:
            s0 = m.start(3)
        infos.append(dict(word=info["word"], t=info["t"], year=year, num=num,
                          span=(s0, m.end())))
        end = m.end()
    return end, infos


KNOWN_TYPOS = {
    ("reg", 2204, 1348): ("reg", 2024, 1348),  # refuso GU (1347, nota 30)
    ("reg", 2019, 1986): ("reg", 2019, 1896),  # refuso GU (1351, art. 7): Frontex
    ("dir", 2024, 1436): ("dir", 2024, 1346),  # refuso GU (1359): direttiva accoglienza
}


def act_target(reg, info):
    """Ritorna (kind, key, href): kind in {corpus, extlocal, ext}."""
    base = info["t"].split("_")[0]
    fixed = KNOWN_TYPOS.get((base, info["year"], info["num"]))
    if fixed:
        base, info = fixed[0], dict(info, t=fixed[0], year=fixed[1], num=fixed[2])
    key = CORPUS.get((base, info["year"], info["num"]))
    if key and info["t"] == base:
        return "corpus", key, page_for(key)
    ext = EXT.get((info["t"], info["year"], info["num"]))
    if ext:
        return "extlocal", ext["key"], ext["page"]
    return "ext", None, eurlex_url(info["t"], info["year"], info["num"])


def consume_qualifiers(text, i):
    """consuma lettera/punto/comma/frase (senza link)."""
    while True:
        for rx in (RE_LETT_Q, RE_PUNTO_Q, RE_COMMA_Q, RE_FRASE_Q):
            m = rx.match(text, i)
            if m:
                i = m.end()
                break
        else:
            return i


def parse_paragraph_block(text, i):
    """dopo 'articolo N': prova ', paragrafo M' (singolo) o ', paragrafi M e P'.
    Ritorna (i, single_par or None, [(num,start,end)...])."""
    m = RE_PAR_Q.match(text, i)
    if not m:
        return i, None, []
    plural = m.group(1) == "i"
    i = m.end()
    nums = []
    while True:
        mn = RE_NUM.match(text, i)
        if not mn:
            break
        nums.append((int(mn.group(1)), mn.start(1), mn.end()))
        i = mn.end()
        ms = RE_LIST_SEP.match(text, i)
        if not ms:
            break
        i = ms.end()
        if not plural:
            break
    if not nums:
        return i, None, []
    if not plural and len(nums) == 1:
        return i, nums[0], nums
    return i, None, nums


def parse_group(text, start, act):
    """Un gruppo 'articolo N[, paragrafo M]' / 'articoli A, B e C' / 'articoli da X a Y'.
    Ritorna dict o None."""
    m = RE_ART.match(text, start)
    if not m:
        return None
    plural = m.group(1) == "i"
    i = m.end()
    items = []  # (num, suffisso, numstart, numend)
    while True:
        mr = RE_RANGE.match(text, i)
        if mr and plural:
            items.append((int(mr.group(1)), None, mr.start(1), mr.start(1) + len(mr.group(1))))
            items.append((int(mr.group(2)), None, mr.start(2), mr.start(2) + len(mr.group(2))))
            i = mr.end()
        else:
            mn = RE_NUM.match(text, i)
            if not mn:
                break
            suff = mn.group(2)
            items.append((int(mn.group(1)), re.sub(r"^[\s-]+", "", suff) if suff else None,
                          mn.start(1), mn.end()))
            i = mn.end()
        if not plural:
            break
        ms = RE_LIST_SEP_X.match(text, i)
        if not ms:
            break
        i = ms.end()
    if not items:
        return None
    single = (not plural) and len(items) == 1
    par_single, par_list = None, []
    if single:
        i, par_single, par_list = parse_paragraph_block(text, i)
        i = consume_qualifiers(text, i)
        # continuazione: «articolo 42, paragrafo 1, lettera f), e paragrafo 5, lettera b)»
        # — i paragrafi successivi appartengono allo stesso articolo
        while par_list:
            mq = RE_PAR_CONT.match(text, i)
            if not mq:
                break
            jj = mq.end()
            extra = []
            while True:
                mn = RE_NUM.match(text, jj)
                if not mn:
                    break
                extra.append((int(mn.group(1)), mn.start(1), mn.end()))
                jj = mn.end()
                ms = RE_LIST_SEP.match(text, jj)
                if not ms:
                    break
                jj = ms.end()
            if not extra:
                break
            jj2 = consume_qualifiers(text, jj)
            # «e paragrafo 5 dell'articolo 50» / «di detto articolo»: altro articolo,
            # lascia al parser dei paragrafi standalone
            if RE_DELL_ARTICOLO.match(text, jj2) or RE_STESSO_ART.match(text, jj2):
                break
            par_list.extend(extra)
            i = jj2
        if len(par_list) > 1:
            par_single = None
    else:
        m2 = RE_PAR_Q.match(text, i)
        if m2:
            i, _, _ = parse_paragraph_block(text, i)
            AUDIT.issue(act["key"], "qualificatore-paragrafo-dopo-elenco (linkati solo gli articoli)",
                        text[max(0, start - 20):i + 30])
        i = consume_qualifiers(text, i)
    return dict(start=start, end=i, items=items, plural=plural, single=single,
                par_single=par_single, par_list=par_list)


def parse_tail(text, j, ctx, reg, act):
    """Coda di una catena di citazioni: a quale atto appartengono gli articoli?
    Ritorna dict(kind=..., end=..., ...)."""
    mp = RE_PRESENTE.match(text, j)
    if mp:
        return dict(kind="self", explicit=True, end=mp.end())
    act_pos = None
    ma = RE_ACT_TAIL.match(text, j)
    if ma:
        act_pos = ma.end()
    else:
        # refuso ricorrente: «articolo 41 regolamento (UE) 2024/1351» senza «del»
        mb = re.compile(r"\s+(?=(?:regolament|direttiv|decision))").match(text, j)
        if mb:
            probe_end, probe = parse_act_ref(text, mb.end())
            if probe:
                act_pos = mb.end()
    if act_pos is not None:
        a_end, infos = parse_act_refs(text, act_pos)
        if infos:
            act_emits = []
            first = None
            for info in infos:
                kind, key, href = act_target(reg, info)
                if kind == "ext":
                    act_emits.append(Emit(info["span"][0], info["span"][1], href, ext="1"))
                else:
                    act_emits.append(Emit(info["span"][0], info["span"][1], href, act=key))
                ctx["last_act"] = (kind, key if key else href)
                if first is None:
                    first = (kind, key, href)
            kind, key, href = first
            if kind == "ext":
                return dict(kind="ext", explicit=True, end=a_end, url=href,
                            act_emits=act_emits)
            return dict(kind=kind, explicit=True, end=a_end, key=key,
                        act_emits=act_emits)
        if not re.match(r"\s*(?:decisione|direttiva|regolamento)\s+di\s+cui", text[j:j + 40],
                        re.IGNORECASE):
            AUDIT.issue(act["key"], "coda-atto-non-riconosciuta", text[max(0, j - 60):j + 70])
        return dict(kind="none", explicit=False, end=j)
    mt = RE_TFUE.match(text, j) or None
    if mt:
        return dict(kind="treaty", explicit=True, end=mt.end(),
                    treaty="TFUE" if mt.group(1) == "TFUE" else "TUE")
    mtf = RE_TRATTATO_F.match(text, j)
    if mtf:
        return dict(kind="treaty", explicit=True, end=mtf.end(), treaty="TFUE")
    mtu = RE_TRATTATO_U.match(text, j)
    if mtu:
        return dict(kind="treaty", explicit=True, end=mtu.end(), treaty="TUE")
    mc = RE_CARTA.match(text, j)
    if mc:
        return dict(kind="carta", explicit=True, end=mc.end())
    mf = RE_REG_FIN.match(text, j)
    if mf:
        return dict(kind="ext", explicit=True, end=mf.end(),
                    url=eurlex_url("reg", 2018, 1046))
    msk = RE_SKIP_TAIL.match(text, j)
    if msk:
        return dict(kind="skip", explicit=True, end=j,
                    reason="atto non collegabile (protocollo/convenzione/accordo)")
    mst = RE_STESSO.match(text, j)
    if mst:
        last = ctx.get("last_act")
        if last and last[0] in ("corpus", "extlocal"):
            return dict(kind=last[0], explicit=True, end=mst.end(), key=last[1])
        if last and last[0] == "ext":
            return dict(kind="ext", explicit=True, end=mst.end(), url=last[1])
        return dict(kind="skip", explicit=True, end=j,
                    reason="'stesso/tale regolamento' senza atto di riferimento")
    return dict(kind="none", explicit=False, end=j)


def emit_group_corpus(g, target_key, reg, act, emits):
    """Emette i link di un gruppo verso un atto del corpus. Ritorna n. link articolo."""
    n_links = 0
    if g["single"]:
        n, suff, s0, e0 = g["items"][0]
        if suff:
            AUDIT.issue(act["key"], f"articolo {n} {suff}: numerazione bis/ter assente nel corpus",
                        "…")
            return 0
        par = g["par_single"][0] if g["par_single"] else None
        href, par_eff = art_href(reg, target_key, n, par)
        if not href:
            return -n  # segnale: articolo inesistente
        if g["par_list"] and len(g["par_list"]) > 1:
            href_art, _ = art_href(reg, target_key, n, None)
            emits.append(Emit(g["start"], e0, href_art, act=target_key, art=str(n)))
            n_links += 1
            for (pn, ps, pe) in g["par_list"]:
                hp, pe_eff = art_href(reg, target_key, n, pn)
                if hp and pe_eff:
                    emits.append(Emit(ps, pe, hp, act=target_key, art=str(n), par=str(pn)))
                    n_links += 1
        else:
            span_end = g["par_single"][2] if (g["par_single"] and par_eff) else e0
            emits.append(Emit(g["start"], span_end, href, act=target_key, art=str(n),
                              **(dict(par=str(par_eff)) if par_eff else {})))
            n_links += 1
    else:
        for (n, suff, s0, e0) in g["items"]:
            if suff:
                continue
            href, _ = art_href(reg, target_key, n, None)
            if href:
                emits.append(Emit(s0, e0, href, act=target_key, art=str(n)))
                n_links += 1
            else:
                return -n
    return n_links


def emit_group_ext(g, ext, act, emits, text):
    """Emette i link di un gruppo verso un atto esterno scaricato.
    Articolo trovato → ancora; non trovato → pagina dell'atto."""
    n_links = 0
    page = ext["page"]
    for idx, (n, suff, s0, e0) in enumerate(g["items"]):
        artkey = ext_artkey(n, suff)
        info = ext["arts"].get(artkey) if artkey else None
        single_span = g["single"] and idx == 0
        span_start = g["start"] if single_span else s0
        span_end = e0
        par = None
        if single_span and g["par_single"] and not (g["par_list"] and len(g["par_list"]) > 1):
            span_end = g["par_single"][2]
            par = g["par_single"][0]
        if info:
            data = dict(act=ext["key"], art=artkey)
            if par:
                data["par"] = str(par)
            emits.append(Emit(span_start, span_end, f"{page}#{info['anchor']}", **data))
            n_links += 1
            if single_span and g["par_list"] and len(g["par_list"]) > 1:
                for (pn, ps, pe) in g["par_list"]:
                    emits.append(Emit(ps, pe, f"{page}#{info['anchor']}",
                                      act=ext["key"], art=artkey, par=str(pn)))
                    n_links += 1
        else:
            emits.append(Emit(span_start, span_end, page, act=ext["key"]))
            AUDIT.issue(act["key"],
                        f"articolo {n}{' ' + suff if suff else ''} non trovato in {ext['key']}: "
                        f"link alla pagina dell'atto",
                        text[max(0, s0 - 40):e0 + 60])
    return n_links


def parse_article_citation(text, start, ctx, reg, act):
    """Catena di citazioni: 'articolo A, ..., l'articolo B, ... e gli articoli C e D'
    con eventuale coda comune ('del regolamento (UE) ...', 'TFUE', ...).
    Ritorna (end, [Emit], handled)."""
    groups = []
    pos = start
    while True:
        g = parse_group(text, pos, act)
        if not g:
            break
        groups.append(g)
        mc = RE_CHAIN.match(text, g["end"])
        if not mc:
            break
        pos = mc.start() + len(mc.group(0))
    if not groups:
        return start, [], False
    j = groups[-1]["end"]
    tail = parse_tail(text, j, ctx, reg, act)
    end = max(j, tail["end"])
    noref = ctx.get("quote") or ctx.get("amend")

    emits = []
    # link agli atti nominati in coda (sempre, anche in contesto di modifica)
    if tail.get("act_emits"):
        emits.extend(tail["act_emits"])
        AUDIT.count(act["key"], "atti", len(tail["act_emits"]))

    # in contesto «testo citato» o «articolo di modifica», i riferimenti senza coda
    # e quelli al «presente regolamento» appartengono all'atto modificato: niente link
    if noref and (not tail["explicit"] or tail["kind"] == "self"):
        AUDIT.issue(act["key"], "rif. in contesto di modifica: non linkato",
                    text[max(0, start - 40):end + 40])
        return end, emits, True

    if tail["kind"] == "skip":
        AUDIT.issue(act["key"], tail["reason"], text[max(0, start - 30):end + 60])
        return end, emits, True

    if tail["kind"] == "treaty":
        for g in groups:
            for (n, suff, s0, e0) in g["items"]:
                u = (TFUE_URL if tail["treaty"] == "TFUE" else TUE_URL).format(art=n)
                emits.append(Emit(s0 if g["plural"] or len(groups) > 1 else g["start"],
                                  e0, u, ext="1"))
        AUDIT.count(act["key"], "trattati", sum(len(g["items"]) for g in groups))
        ctx["last_art"] = None  # antecedente non ancorabile per «detto articolo»
        return end, emits, True

    if tail["kind"] == "carta":
        for g in groups:
            emits.append(Emit(g["start"], g["end"], CARTA_URL, ext="1"))
        AUDIT.count(act["key"], "carta", len(groups))
        ctx["last_art"] = None
        return end, emits, True

    if tail["kind"] == "ext":
        for g in groups:
            emits.append(Emit(g["start"], g["end"], tail["url"], ext="1"))
        AUDIT.count(act["key"], "art-esterni", len(groups))
        ctx["last_art"] = None
        return end, emits, True

    if tail["kind"] == "extlocal":
        ext = EXT_BY_KEY[tail["key"]]
        n_links = 0
        for g in groups:
            n_links += emit_group_ext(g, ext, act, emits, text)
        if n_links:
            AUDIT.count(act["key"], "art-ext-loc", n_links)
            for g in reversed(groups):
                ak = next((ext_artkey(n, suff) for (n, suff, s0, e0) in reversed(g["items"])
                           if ext_artkey(n, suff) in ext["arts"]), None)
                if ak:
                    ctx["last_art"] = ("extlocal", ext["key"], ak)
                    break
        return end, emits, True

    if tail["kind"] == "none" and ctx.get("cit"):
        # nel preambolo («visto il TFUE, in particolare l'articolo 78...») i riferimenti
        # senza coda sono articoli del trattato
        for g in groups:
            for (n, suff, s0, e0) in g["items"]:
                emits.append(Emit(s0 if g["plural"] or len(groups) > 1 else g["start"],
                                  e0, TFUE_URL.format(art=n), ext="1"))
        AUDIT.count(act["key"], "trattati", sum(len(g["items"]) for g in groups))
        return end, emits, True

    target_key = tail["key"] if tail["kind"] == "corpus" else act["key"]
    cross = target_key != act["key"]

    # sicurezza: una catena senza coda con numeri che non esistono in questo atto
    # è quasi certamente un rinvio a un altro atto → meglio nessun link che un link errato
    if tail["kind"] == "none":
        t = reg[target_key]
        missing = [n for g in groups for (n, suff, s0, e0) in g["items"]
                   if not suff and n not in t["arts"]]
        if missing:
            AUDIT.issue(act["key"],
                        f"rinvio senza coda con articoli estranei a {target_key} "
                        f"({', '.join(map(str, missing))}): non linkato",
                        text[max(0, groups[0]["start"] - 50):end + 60])
            return end, emits, True

    total = 0
    for g in groups:
        r = emit_group_corpus(g, target_key, reg, act, emits)
        if r < 0:
            AUDIT.issue(act["key"], f"articolo {-r} inesistente in {target_key}",
                        text[max(0, g["start"] - 40):end + 40])
        else:
            total += r
    if total:
        AUDIT.count(act["key"], "art-cross" if cross else "art-interni", total)
        t = reg[target_key]
        for g in reversed(groups):
            n_last = next((n for (n, suff, s0, e0) in reversed(g["items"])
                           if not suff and n in t["arts"]), None)
            if n_last is not None:
                ctx["last_art"] = ("corpus", target_key, n_last)
                break
    return end, emits, True


def _emit_pars(nums, target, reg, act, emits, text, start):
    """emette i link per numeri di paragrafo verso (kind, key, art). Ritorna n. link."""
    kind, tkey, tart = target
    n_ok = 0
    if kind == "corpus":
        for (pn, ps, pe) in nums:
            href, par_eff = art_href(reg, tkey, tart, pn)
            if href and par_eff:
                emits.append(Emit(ps, pe, href, act=tkey, art=str(tart), par=str(pn)))
                n_ok += 1
            elif href:
                # niente ancora a livello di paragrafo → ripiega sull'articolo
                emits.append(Emit(ps, pe, href, act=tkey, art=str(tart)))
                n_ok += 1
            else:
                AUDIT.issue(act["key"],
                            f"paragrafo {pn} dell'articolo {tart} ({tkey}): articolo assente",
                            text[max(0, start - 40):pe + 40])
    else:  # extlocal
        ext = EXT_BY_KEY[tkey]
        artkey = str(tart)
        info = ext["arts"].get(artkey)
        for (pn, ps, pe) in nums:
            if info:
                emits.append(Emit(ps, pe, f"{ext['page']}#{info['anchor']}",
                                  act=tkey, art=artkey, par=str(pn)))
                n_ok += 1
            else:
                emits.append(Emit(ps, pe, ext["page"], act=tkey))
                AUDIT.issue(act["key"],
                            f"articolo {artkey} non trovato in {tkey}: link alla pagina dell'atto",
                            text[max(0, start - 40):pe + 40])
    return n_ok


def parse_standalone_paragraph(text, start, ctx, reg, act):
    """«paragrafo N[, qualificatori]» eventualmente in catena
    («al paragrafo 7, lettera a), o al paragrafo 7, lettera b)») con coda comune:
    nulla → articolo contenitore; «del presente articolo»; «di detto/tale articolo»
    (anafora → last_art); «dell'articolo M [del regolamento X | di tale regolamento]»."""
    groups = []
    pos = start
    while True:
        m = RE_PARAGRAFO_STANDALONE.match(text, pos)
        if not m:
            break
        plural = m.group(1) == "i"
        i = m.end()
        nums = []
        while True:
            mn = RE_NUM.match(text, i)
            if not mn:
                break
            nums.append((int(mn.group(1)), mn.start(1), mn.end()))
            i = mn.end()
            if not plural:
                break
            ms = RE_LIST_SEP.match(text, i)
            if not ms:
                break
            i = ms.end()
        if not nums:
            break
        i = consume_qualifiers(text, i)
        groups.append((nums, i))
        mc = RE_PAR_CHAIN.match(text, i)
        if not mc:
            break
        pos = mc.end()
    if not groups:
        return start, [], False
    nums_all = [t for g, _ in groups for t in g]
    i = groups[-1][1]

    # coda comune
    target = None
    end = i
    art_extra = None  # (numstart, numend) per «dell'articolo M» esplicito
    md = RE_DELL_ARTICOLO.match(text, i)
    mpres = RE_PRES_ART.match(text, i)
    mstesso = RE_STESSO_ART.match(text, i)
    if mpres:
        end = mpres.end()
    elif mstesso:
        la = ctx.get("last_art")
        if la:
            target = la
            end = mstesso.end()
        else:
            AUDIT.issue(act["key"],
                        "paragrafo di 'detto/tale articolo' senza antecedente: non linkato",
                        text[max(0, start - 50):mstesso.end() + 30])
            return mstesso.end(), [], True
    elif md:
        mn = RE_NUM.match(text, md.end())
        if mn:
            n_art = int(mn.group(1))
            suff = re.sub(r"^[\s-]+", "", mn.group(2)) if mn.group(2) else None
            k = mn.end()
            k2 = consume_qualifiers(text, k)
            mp2 = RE_PRESENTE.match(text, k2)
            mst2 = RE_STESSO.match(text, k2)
            ma2 = RE_ACT_TAIL.match(text, k2)
            target = ("corpus", act["key"], n_art)
            end = k
            if mp2:
                end = mp2.end()
            elif mst2:
                last = ctx.get("last_act")
                if last and last[0] == "corpus":
                    target = ("corpus", last[1], n_art)
                    end = mst2.end()
                elif last and last[0] == "extlocal":
                    target = ("extlocal", last[1], ext_artkey(n_art, suff) or str(n_art))
                    end = mst2.end()
                else:
                    AUDIT.issue(act["key"],
                                "'di tale regolamento' senza antecedente (paragrafo): non linkato",
                                text[max(0, start - 40):mst2.end() + 30])
                    return mst2.end(), [], True
            elif ma2:
                a_end, info = parse_act_ref(text, ma2.end())
                if info:
                    kind, key, href = act_target(reg, info)
                    if kind == "corpus":
                        target = ("corpus", key, n_art)
                        end = a_end
                    elif kind == "extlocal":
                        target = ("extlocal", key, ext_artkey(n_art, suff) or str(n_art))
                        end = a_end
                    else:
                        return start, [], False  # atto solo EUR-Lex → all'handler atti
            if suff and target[0] == "corpus":
                AUDIT.issue(act["key"], f"articolo {n_art} {suff}: bis/ter assente nel corpus",
                            text[max(0, start - 30):end + 30])
                return end, [], True
            art_extra = (mn.start(1), mn.end())
    if target is None:
        if ctx.get("article") is None:
            AUDIT.issue(act["key"], "paragrafo senza articolo di contesto",
                        text[max(0, start - 40):i + 40])
            return end, [], True
        target = ("corpus", act["key"], ctx["article"])

    emits = []
    n_ok = _emit_pars(nums_all, target, reg, act, emits, text, start)
    if art_extra:
        s0, e0 = art_extra
        kind, tkey, tart = target
        if kind == "corpus":
            href, _ = art_href(reg, tkey, tart, None)
            if href:
                emits.append(Emit(s0, e0, href, act=tkey, art=str(tart)))
        else:
            ext = EXT_BY_KEY[tkey]
            info = ext["arts"].get(str(tart))
            if info:
                emits.append(Emit(s0, e0, f"{ext['page']}#{info['anchor']}",
                                  act=tkey, art=str(tart)))
    if emits:
        AUDIT.count(act["key"], "paragrafi", n_ok)
        ctx["last_art"] = target
    return end, emits, True


def parse_considerando(text, start, ctx, reg, act):
    m = RE_CONSIDERANDO.match(text, start)
    if not m:
        return start, [], False
    i = m.end()
    nums = []
    while True:
        mn = RE_NUM.match(text, i)
        if not mn:
            break
        nums.append((int(mn.group(1)), mn.start(1), mn.end()))
        i = mn.end()
        ms = RE_LIST_SEP.match(text, i)
        if not ms:
            break
        i = ms.end()
    if not nums:
        return start, [], False
    # coda atto: "considerando 12 del regolamento ..." → ritarget o salto
    target = act
    end = i
    ma = RE_ACT_TAIL.match(text, i)
    if ma:
        a_end, info = parse_act_ref(text, ma.end())
        if info:
            kind, key, href = act_target(reg, info)
            if kind == "corpus":
                target = reg[key]
                end = a_end
            else:
                AUDIT.issue(act["key"], "considerando di atto esterno: non linkato",
                            text[max(0, start - 20):a_end + 20])
                return a_end, [], True
    emits = []
    for (n, s0, e0) in nums:
        if n in target["rcts"]:
            emits.append(Emit(s0, e0, f"{page_for(target['key'])}#{target['rcts'][n]}",
                              act=target["key"], rct=str(n)))
    if emits:
        AUDIT.count(act["key"], "considerando", len(emits))
        return end, emits, True
    return start, [], False


def parse_allegato(text, start, ctx, reg, act):
    m = RE_ALLEGATO.match(text, start)
    if not m:
        return start, [], False
    i = m.end()
    mr = re.compile(r"([IVX]+|\d+)\b").match(text, i)
    if not mr:
        return start, [], False
    roman = mr.group(1).upper()
    i = mr.end()
    end = i
    target_key = act["key"]
    external = None
    explicit = False
    mp = RE_PRESENTE.match(text, i)
    ma = RE_ACT_TAIL.match(text, i)
    if mp:
        end = mp.end()
        explicit = True
    elif ma:
        a_end, info = parse_act_ref(text, ma.end())
        if info:
            kind, key, href = act_target(reg, info)
            if kind == "corpus":
                target_key = key
            elif kind == "extlocal":
                external = ("local", href, key)
            else:
                external = ("ext", href, None)
            end = a_end
            explicit = True
    noref = ctx.get("quote") or ctx.get("amend")
    if noref and not (external or (explicit and target_key != act["key"])):
        AUDIT.issue(act["key"], "allegato in contesto di modifica: non linkato",
                    text[max(0, start - 30):end + 40])
        return end, [], True
    if external:
        if external[0] == "local":
            return end, [Emit(start, end, external[1], act=external[2])], True
        return end, [Emit(start, end, external[1], ext="1")], True
    t = reg.get(target_key)
    if t and roman in t["anxs"]:
        return end, [Emit(start, mr.end(), f"{page_for(target_key)}#{t['anxs'][roman]}",
                          act=target_key, anx=roman)], True
    AUDIT.issue(act["key"], f"allegato {roman} non trovato in {target_key}",
                text[max(0, start - 30):end + 30])
    return end, [], True


def find_section(act, kind, roman, part_ctx):
    cands = [s for s in act["sections"] if s["kind"] == kind and s["roman"] == roman]
    if not cands:
        return None
    if kind == "CAPO" and len(cands) > 1:
        if part_ctx:
            for s in cands:
                if s["part"] == part_ctx:
                    return s
        return None
    return cands[0]


def parse_parte_capo(text, start, ctx, reg, act, which):
    rx = RE_PARTE if which == "PARTE" else RE_CAPO
    m = rx.match(text, start)
    if not m:
        return start, [], False
    roman = m.group(1)
    i = m.end()
    part_ctx = ctx.get("part")
    end = i
    if which == "CAPO":
        md = RE_DELLA_PARTE.match(text, i)
        mp = RE_PRES_PARTE.match(text, i)
        if md:
            part_ctx = md.group(1).upper()
            end = md.end()
            i = end
        elif mp:
            end = mp.end()
            i = end
    # coda atto: «capo II del regolamento (UE) 2019/817»
    target = act
    external = None
    explicit = False
    mpres = RE_PRESENTE.match(text, i)
    ma = RE_ACT_TAIL.match(text, i)
    if mpres:
        end = mpres.end()
        explicit = True
    elif ma:
        a_end, info = parse_act_ref(text, ma.end())
        if info:
            kind, key, href = act_target(reg, info)
            if kind == "corpus":
                target = reg[key]
                part_ctx = part_ctx if key == act["key"] else (
                    md.group(1).upper() if which == "CAPO" and md else None)
            elif kind == "extlocal":
                external = ("local", href, key)
            else:
                external = ("ext", href, None)
            end = a_end
            explicit = True
    noref = ctx.get("quote") or ctx.get("amend")
    if noref and not (external or (explicit and target is not act)):
        return end, [], True
    if external:
        if external[0] == "local":
            return end, [Emit(start, end, external[1], act=external[2])], True
        return end, [Emit(start, end, external[1], ext="1")], True
    if which == "CAPO":
        sec = find_section(target, "CAPO", roman, part_ctx if target is act else part_ctx)
    else:
        sec = find_section(target, "PARTE", roman, None)
    if not sec:
        AUDIT.issue(act["key"], f"{which.lower()} {roman} non risolto in {target['key']} "
                    f"(parte ctx={part_ctx})", text[max(0, start - 40):end + 40])
        return end, [], True
    emits = [Emit(start, m.end(), f"{page_for(target['key'])}#{sec['id']}",
                  act=target["key"], sec=sec["id"])]
    AUDIT.count(act["key"], "parti-capi")
    return end, emits, True


MASTER = re.compile(
    r"articol[oi]\s+(?=\d|da\s)|regolament[oi]\b|direttiv[ae]\b|decision[ei]\b|"
    r"considerando\s+(?=\d)|allegat[oi]\s+(?=[IVX\d])|paragraf[oi]\s+(?=\d)|"
    r"\bparte\s+(?=[IVX])|\bcapo\s+(?=[IVX])",
    re.IGNORECASE)


def scan_text(text, ctx, reg, act):
    """Ritorna lista di Emit per questo nodo di testo."""
    emits = []
    pos = 0
    noref = ctx.get("quote") or ctx.get("amend")
    while True:
        m = MASTER.search(text, pos)
        if not m:
            break
        token = m.group(0).lower()
        s = m.start()
        if token.startswith("articol"):
            end, es, handled = parse_article_citation(text, s, ctx, reg, act)
        elif token.startswith(("regolament", "direttiv", "decision")):
            a_end, infos = parse_act_refs(text, s)
            if infos:
                for info in infos:
                    kind, key, href = act_target(reg, info)
                    if kind == "ext":
                        emits.append(Emit(info["span"][0], info["span"][1], href, ext="1"))
                        ctx["last_act"] = ("ext", href)
                    else:
                        emits.append(Emit(info["span"][0], info["span"][1], href, act=key))
                        ctx["last_act"] = (kind, key)
                AUDIT.count(act["key"], "atti", len(infos))
                pos = a_end
                continue
            pos = m.end()
            continue
        elif token.startswith("considerando"):
            if noref:
                pos = m.end(); continue
            end, es, handled = parse_considerando(text, s, ctx, reg, act)
        elif token.startswith("allegat"):
            end, es, handled = parse_allegato(text, s, ctx, reg, act)
        elif token.startswith("paragraf"):
            if noref:
                pos = m.end(); continue
            end, es, handled = parse_standalone_paragraph(text, s, ctx, reg, act)
        else:  # parte / capo
            which = "PARTE" if token.startswith("parte") else "CAPO"
            end, es, handled = parse_parte_capo(text, s, ctx, reg, act, which)
        if not handled:
            pos = m.end()
            continue
        emits.extend(es)
        pos = max(end, m.end())
    return emits


# ---------------------------------------------------------------- riscrittura

def has_excluded_ancestor(node):
    p = node.parent
    while p is not None and p.name != "[document]":
        if p.name == "a":
            return True
        classes = set(p.get("class", []) if isinstance(p, Tag) else [])
        if classes & EXCLUDED_CLASSES:
            return True
        p = p.parent
    return False


def node_context(node, act):
    ctx = {}
    p = node.parent
    while p is not None and p.name != "[document]":
        if isinstance(p, Tag):
            classes = set(p.get("class", []))
            if "oj-quotation" in classes:
                ctx["quote"] = True
            pid = p.get("id", "")
            if pid.startswith("art_") and "article" not in ctx:
                if pid in act.get("amend_ids", set()):
                    ctx["amend"] = True
                try:
                    ctx["article"] = int(pid[4:])
                except ValueError:
                    pass
            if pid.startswith("cit_"):
                ctx["cit"] = True
            if "scope" not in ctx and re.match(r"^(art_|rct_|cit_|anx)", pid):
                ctx["scope"] = pid
        p = p.parent
    return ctx


def link_act_text(act, reg):
    for root in [act["container"]] + act["anx_els"]:
        # le tavole di concordanza citano in colonna due atti diversi: non linkabile
        title = root.find(class_="oj-doc-ti")
        if title and root is not act["container"]:
            full = " ".join(p.get_text(" ", strip=True)
                            for p in root.find_all("p", class_="oj-doc-ti"))
            if "concordanza" in full.lower():
                continue
        link_container(root, act, reg)


def link_container(container, act, reg):
    # contesto "parte" per la risoluzione dei capi: camminata in ordine di documento
    part_by_node = {}
    cur_part = None
    for el in container.descendants:
        if isinstance(el, Tag) and "oj-ti-section-1" in (el.get("class") or []):
            t = el.get_text(" ", strip=True)
            mm = re.match(r"PARTE\s+([IVX]+)", t, re.IGNORECASE)
            if mm:
                cur_part = mm.group(1).upper()
        elif isinstance(el, NavigableString):
            part_by_node[id(el)] = cur_part

    nodes = [n for n in container.find_all(string=True)
             if n.strip() and not has_excluded_ancestor(n)]
    soup = act["soup"]
    carry_scope, carry_last, carry_last_art = None, None, None
    for node in nodes:
        text = str(node)
        ctx = node_context(node, act)
        ctx["part"] = part_by_node.get(id(node))
        # «di tale regolamento» / «di detto articolo» possono riferirsi a un atto o
        # articolo citato poco prima, nella stessa unità (articolo/considerando)
        if ctx.get("scope") == carry_scope:
            if carry_last:
                ctx["last_act"] = carry_last
            if carry_last_art:
                ctx["last_art"] = carry_last_art
        emits = scan_text(text, ctx, reg, act)
        carry_scope = ctx.get("scope")
        carry_last = ctx.get("last_act")
        carry_last_art = ctx.get("last_art")
        if not emits:
            continue
        emits.sort(key=lambda e: (e.start, -(e.end - e.start)))
        # rimuovi sovrapposizioni
        clean, last_end = [], -1
        for e in emits:
            if e.start >= last_end:
                clean.append(e)
                last_end = e.end
        pieces = []
        cur = 0
        for e in clean:
            if e.start > cur:
                pieces.append(NavigableString(text[cur:e.start]))
            a = soup.new_tag("a", href=e.href)
            a["class"] = [e.cls] + (["ext"] if e.data.get("ext") else [])
            for k, v in e.data.items():
                if k != "ext":
                    a[f"data-{k}"] = v
            if e.data.get("ext"):
                a["target"] = "_blank"
                a["rel"] = "noopener"
            a.string = text[e.start:e.end]
            pieces.append(a)
            cur = e.end
        if cur < len(text):
            pieces.append(NavigableString(text[cur:]))
        node.replace_with(*pieces)


# ---------------------------------------------------------------- override manuali

def _override_href(reg, t):
    """href per un target di override {act, art?, par?} (corpus o atto esterno)."""
    akey = t.get("act")
    if akey in reg:
        if t.get("art"):
            href, _ = art_href(reg, akey, int(t["art"]), int(t["par"]) if t.get("par") else None)
            return href
        return page_for(akey)
    ext = EXT_BY_KEY.get(akey)
    if ext:
        art = str(t.get("art", ""))
        if art and art in ext["arts"]:
            return f"{ext['page']}#{ext['arts'][art]['anchor']}"
        return ext["page"]
    return t.get("href")


def apply_overrides(reg):
    """Correzioni puntuali da overrides.json: casi in cui la semantica del rinvio
    non è decidibile dalla grammatica. Ogni regola:
      {"act": "1356", "where": "005.003", "text": "articolo 6", "nth": 1,
       "target": {"act": "reg-2016-399", "art": "6", "par": "5"}}   oppure "unlink": true
    `where` è l'id del div che contiene il link (paragrafo o articolo)."""
    fp = BASE / "overrides.json"
    if not fp.exists():
        return 0
    rules = json.load(open(fp, encoding="utf-8"))
    n_applied = 0
    for rule in rules:
        a = reg.get(rule["act"])
        if not a:
            print(f"  OVERRIDE IGNORATO (atto sconosciuto): {rule}")
            continue
        roots = [a["container"]] + a["anx_els"]
        where = rule.get("where")
        wanted = norm(rule["text"])
        nth = rule.get("nth", 1)
        found = 0
        done = False
        for root in roots:
            scope_el = root.find(id=where) if where else root
            if scope_el is None:
                continue
            for link in scope_el.find_all("a", class_="xref"):
                if re.sub(r"\s+", " ", norm(link.get_text())) != re.sub(r"\s+", " ", wanted):
                    continue
                found += 1
                if found != nth:
                    continue
                if rule.get("unlink"):
                    link.replace_with(NavigableString(link.get_text()))
                else:
                    t = rule["target"]
                    href = _override_href(reg, t)
                    if not href:
                        print(f"  OVERRIDE SENZA HREF VALIDO: {rule}")
                        break
                    for attr in [k for k in link.attrs if k.startswith("data-")]:
                        del link[attr]
                    link["href"] = href
                    link["class"] = ["xref"] + (["ext"] if t.get("ext") else [])
                    if t.get("ext"):
                        link["target"] = "_blank"
                        link["rel"] = "noopener"
                    else:
                        for k in ("act", "art", "par", "rct", "anx", "sec"):
                            if t.get(k):
                                link[f"data-{k}"] = str(t[k])
                        # un override verso un anchor di paragrafo inesistente ripiega
                        # sull'articolo: niente data-par se l'ancora non è di paragrafo
                        if t.get("par") and not re.search(r"#\d+\.\d+$", href):
                            pass  # data-par resta: il tooltip evidenzia comunque il paragrafo
                n_applied += 1
                done = True
                break
            if done:
                break
        if not done:
            print(f"  OVERRIDE NON APPLICATO (link non trovato): {rule}")
    return n_applied


# ---------------------------------------------------------------- dati JS

def clean_copy_html(el):
    """copia html di un elemento per i pannelli: via gli id, via i link nota."""
    frag = BeautifulSoup(str(el), "lxml")
    for t in frag.find_all(True):
        if t.has_attr("id"):
            del t["id"]
    for a in frag.find_all("a", href=re.compile(r"^#nt[rc]")):
        sup = frag.new_tag("span")
        sup["class"] = "fn-mark"
        sup.string = a.get_text(strip=True)
        a.replace_with(sup)
    body = frag.find("body")
    inner = "".join(str(c) for c in (body.contents if body else frag.contents))
    return inner.strip()


def extract_frags(act):
    """per ogni articolo: lista di frammenti [parNum|null, html]"""
    arts_data = {}
    for n, info in act["arts"].items():
        el = info["el"]
        frags = []
        for child in el.children:
            if not isinstance(child, Tag):
                continue
            classes = set(child.get("class", []))
            cid = child.get("id", "")
            if "oj-ti-art" in classes or "eli-title" in classes:
                continue
            m = re.match(r"^(\d+)\.(\d+)$", cid)
            par = int(m.group(2)) if m else None
            frags.append([par, clean_copy_html(child)])
        arts_data[str(n)] = dict(label=info["label"], heading=info["heading"],
                                 anchor=info["id"], frags=frags)
    rct_data = {}
    for n, rid in act["rcts"].items():
        div = act["container"].find(id=rid)
        if div:
            cells = div.find_all("td")
            content = cells[-1] if cells else div
            rct_data[str(n)] = clean_copy_html(content)
    return arts_data, rct_data


# ---------------------------------------------------------------- pagine

def build_toc(act):
    items = ['<a class="toc-h" href="#tit_1">Preambolo e considerando</a>']
    container = act["container"]
    seen_art = set()
    for el in container.descendants:
        if not isinstance(el, Tag):
            continue
        classes = el.get("class") or []
        if "oj-ti-section-1" in classes and el.get("id"):
            txt = el.get_text(" ", strip=True)
            sib = el.find_next("p", class_="oj-ti-section-2")
            sub = sib.get_text(" ", strip=True) if sib else ""
            kind = txt.split()[0].upper() if txt else ""
            cls = "toc-part" if kind == "PARTE" else ("toc-chap" if kind == "CAPO" else "toc-sect")
            items.append(f'<a class="{cls}" href="#{el["id"]}"><b>{txt}</b> {sub}</a>')
        elif el.name == "div" and re.match(r"^art_\d+$", el.get("id", "")) and el["id"] not in seen_art:
            seen_art.add(el["id"])
            n = int(el["id"][4:])
            info = act["arts"].get(n)
            if info:
                h = info["heading"]
                items.append(f'<a class="toc-art" data-art="{el["id"]}" href="#{el["id"]}">'
                             f'<span class="toc-n">{n}</span> {h}</a>')
    for roman, aid in act["anxs"].items():
        items.append(f'<a class="toc-h" href="#{aid}">Allegato {roman}</a>')
    return "\n".join(items)


def page_html(act, toc, nav_links, version=""):
    body = "".join(str(c) for c in act["container"].contents)
    for anx in act["anx_els"]:
        body += '\n<hr class="oj-separator"/>\n' + str(anx)
    short = act["short"]
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{short} — {('Direttiva' if act['typ']=='dir' else 'Regolamento')} (UE) 2024/{act['num']}</title>
<link rel="stylesheet" href="assets/style.css?v={version}">
</head>
<body data-act="{act['key']}">
<header class="topbar">
  <a class="home" href="index.html">&#8962; Indice</a>
  <button id="toc-toggle">Sommario</button>
  <nav class="actnav">{nav_links}</nav>
</header>
<div class="layout">
<nav class="toc" id="toc">
  <div class="toc-title">{short}<br><span>(UE) 2024/{act['num']}</span></div>
  {toc}
</nav>
<main class="doc">
{body}
<p class="disclaimer">Versione di lavoro generata dai testi EUR-Lex (GU UE). Fa fede unicamente il testo pubblicato nella Gazzetta ufficiale.</p>
</main>
</div>
<div id="tip" class="tip" hidden></div>
<aside id="panel" class="panel" hidden>
  <div class="panel-bar">
    <button id="panel-back" class="pbtn" title="Riferimento precedente" hidden>&#8592;</button>
    <div id="panel-crumb" class="crumb"></div>
    <button id="panel-close" class="pbtn" title="Chiudi (Esc)">&#10005;</button>
  </div>
  <div id="panel-body" class="panel-body"></div>
  <div class="panel-foot"><a id="panel-go" href="#">Vai all'articolo &#8594;</a> <a id="panel-eurlex" href="#" target="_blank" rel="noopener" hidden>EUR-Lex &#8599;</a></div>
</aside>
<button id="return-chip" hidden>&#8617; Torna al punto precedente</button>
<script src="assets/data.js?v={version}"></script>
<script src="assets/app.js?v={version}"></script>
</body>
</html>"""


def ext_extract_frags(ext):
    """frammenti per pannelli/tooltip degli articoli di un atto esterno."""
    arts_data = {}
    title_re = re.compile(r"^((oj-)?(s?ti-art)|s?title-article-norm|eli-title)$")
    for artkey, info in ext["arts"].items():
        if info.get("frags_pre") is not None:
            arts_data[artkey] = dict(label=info["label"], heading=info["heading"],
                                     anchor=info["anchor"], frags=info["frags_pre"])
            continue
        frags = []
        for child in info["el"].children:
            if not isinstance(child, Tag):
                continue
            classes = child.get("class") or []
            if any(title_re.match(c) for c in classes):
                continue
            m = re.match(r"^(\d+)\.(\d+)$", child.get("id", ""))
            par = int(m.group(2)) if m else None
            frags.append([par, clean_copy_html(child)])
        arts_data[artkey] = dict(label=info["label"], heading=info["heading"],
                                 anchor=info["anchor"], frags=frags)
    return arts_data


def ext_page_html(ext, nav_links, version=""):
    body = ""
    for c in ext["containers"]:
        body += "".join(str(x) for x in c.contents)
    toc_items = []
    for artkey, info in ext["arts"].items():  # ordine del documento
        h = info["heading"]
        num_label = info["label"].replace("Articolo", "").strip()
        toc_items.append(f'<a class="toc-art" data-art="{info["anchor"]}" href="#{info["anchor"]}">'
                         f'<span class="toc-n">{num_label}</span> {h}</a>')
    toc = "\n".join(toc_items)
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{ext['short']} — atto esterno al Patto</title>
<link rel="stylesheet" href="assets/style.css?v={version}">
</head>
<body data-act="{ext['key']}" data-ext-page="1">
<header class="topbar">
  <a class="home" href="index.html">&#8962; Indice</a>
  <button id="toc-toggle">Sommario</button>
  <nav class="actnav">{nav_links}</nav>
</header>
<div class="ext-banner">Atto esterno al Patto — {ext['version']} —
<a href="{ext['eurlex']}" target="_blank" rel="noopener">apri su EUR-Lex &#8599;</a></div>
<div class="layout">
<nav class="toc" id="toc">
  <div class="toc-title">{ext['short']}<br><span>{ext['label'][:90]}</span></div>
  {toc}
</nav>
<main class="doc">
{body}
<p class="disclaimer">Testo riprodotto dal repository dell'Ufficio delle pubblicazioni UE ({ext['version']}).
Fa fede unicamente il testo pubblicato nella Gazzetta ufficiale.</p>
</main>
</div>
<div id="tip" class="tip" hidden></div>
<aside id="panel" class="panel" hidden>
  <div class="panel-bar">
    <button id="panel-back" class="pbtn" title="Riferimento precedente" hidden>&#8592;</button>
    <div id="panel-crumb" class="crumb"></div>
    <button id="panel-close" class="pbtn" title="Chiudi (Esc)">&#10005;</button>
  </div>
  <div id="panel-body" class="panel-body"></div>
  <div class="panel-foot"><a id="panel-go" href="#">Vai all'articolo &#8594;</a> <a id="panel-eurlex" href="#" target="_blank" rel="noopener" hidden>EUR-Lex &#8599;</a></div>
</aside>
<button id="return-chip" hidden>&#8617; Torna al punto precedente</button>
<script src="assets/data.js?v={version}"></script>
<script src="assets/app.js?v={version}"></script>
</body>
</html>"""


def index_html(reg, version=""):
    cards = []
    for a in ACTS:
        act = reg[a["key"]]
        tname = "Direttiva" if a["typ"] == "dir" else "Regolamento"
        n_arts = len(act["arts"])
        title = act["full_title"]
        m = re.search(r"(?:che|recante|sulle|sull['’]|relativ[oa])\s.*$", title, re.IGNORECASE)
        sub = m.group(0) if m else title
        sub = (sub[:220] + "…") if len(sub) > 220 else sub
        cards.append(f"""<a class="card" href="{page_for(a['key'])}">
  <div class="card-num">{tname} (UE) 2024/{a['num']}</div>
  <div class="card-name">{a['title']}</div>
  <div class="card-sub">{sub}</div>
  <div class="card-meta">{n_arts} articoli</div>
</a>""")
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Patto UE migrazione e asilo — testi interattivi</title>
<link rel="stylesheet" href="assets/style.css?v={version}">
</head>
<body class="index">
<main class="idx">
<h1>Patto UE migrazione e asilo</h1>
<p class="idx-sub">I nove regolamenti e la direttiva del Patto in versione interattiva: ogni rinvio normativo è
un collegamento. Passa il mouse su un rinvio per leggere la disposizione citata; clic per aprirla in un
pannello laterale senza perdere il punto di lettura.</p>
<div class="cards">
{''.join(cards)}
</div>
{ext_index_section()}
<p class="disclaimer">Versione di lavoro generata dai testi EUR-Lex (GU UE). Fa fede unicamente il testo pubblicato nella Gazzetta ufficiale.</p>
</main>
</body>
</html>"""


def ext_index_section():
    if not EXT_BY_KEY:
        return ""
    items = []
    for ext in sorted(EXT_BY_KEY.values(), key=lambda e: -e["cites"]):
        items.append(f'<li><a href="{ext["page"]}">{ext["short"]}</a> '
                     f'<span>{ext["label"][:110]} — {ext["version"]}</span></li>')
    return (f'<details class="ext-list"><summary>Atti esterni collegati '
            f'({len(items)}) — testi consultabili nei pannelli e nelle pagine dedicate'
            f'</summary><ul>{"".join(items)}</ul></details>')


def audit_html():
    rows = []
    kinds = ["art-interni", "art-cross", "art-ext-loc", "art-esterni", "atti", "paragrafi",
             "considerando", "parti-capi", "trattati", "carta"]
    head = "".join(f"<th>{k}</th>" for k in kinds)
    tot = defaultdict(int)
    for a in ACTS:
        c = AUDIT.counts[a["key"]]
        cells = "".join(f"<td>{c.get(k, 0)}</td>" for k in kinds)
        for k in kinds:
            tot[k] += c.get(k, 0)
        rows.append(f"<tr><td><b>{a['key']}</b> {a['short']}</td>{cells}</tr>")
    totcells = "".join(f"<td><b>{tot[k]}</b></td>" for k in kinds)
    issues = "".join(
        f"<tr><td>{k}</td><td>{reason}</td><td>{snippet}</td></tr>"
        for (k, reason, snippet) in AUDIT.issues)
    return f"""<!DOCTYPE html>
<html lang="it"><head><meta charset="utf-8"><title>Audit collegamenti</title>
<style>body{{font:14px/1.5 -apple-system,sans-serif;margin:2rem;color:#222}}
table{{border-collapse:collapse;width:100%;margin:1rem 0}}td,th{{border:1px solid #ccc;padding:4px 8px;font-size:13px;text-align:left;vertical-align:top}}
th{{background:#f3f3f3}}</style></head><body>
<h1>Audit dei collegamenti generati</h1>
<h2>Riferimenti linkati per atto</h2>
<table><tr><th>Atto</th>{head}</tr>{''.join(rows)}<tr><td><b>Totale</b></td>{totcells}</tr></table>
<h2>Casi non risolti o saltati ({len(AUDIT.issues)})</h2>
<p>Riferimenti riconosciuti ma non trasformati in link, con il motivo. Da rivedere manualmente se rilevanti.</p>
<table><tr><th>Atto</th><th>Motivo</th><th>Contesto</th></tr>{issues}</table>
</body></html>"""


# ---------------------------------------------------------------- main

def main():
    OUT.mkdir(exist_ok=True)
    global VERSION
    import hashlib
    h = hashlib.sha1()
    for f in ("style.css", "app.js"):
        fp = OUT / "assets" / f
        if fp.exists():
            h.update(fp.read_bytes())
    VERSION = h.hexdigest()[:8]
    (OUT / "assets").mkdir(exist_ok=True)

    print("Caricamento e analisi dei 10 atti…")
    reg = {}
    for a in ACTS:
        load_act(a)
        reg[a["key"]] = a
        print(f"  {a['key']}: {len(a['arts'])} articoli, {len(a['pars'])} paragrafi, "
              f"{len(a['rcts'])} considerando, {len(a['anxs'])} allegati, {len(a['sections'])} sezioni")

    print("Caricamento atti esterni…")
    load_ext_acts()
    print(f"  {len(EXT_BY_KEY)} atti esterni indicizzati "
          f"({sum(len(e['arts']) for e in EXT_BY_KEY.values())} articoli)")

    print("Collegamento dei riferimenti…")
    for a in ACTS:
        link_act_text(a, reg)
        print(f"  {a['key']} fatto")

    n_ov = apply_overrides(reg)
    print(f"  override applicati: {n_ov}")

    print("Estrazione dati per i pannelli…")
    data = {"acts": {}}
    for a in ACTS:
        arts_data, rct_data = extract_frags(a)
        tname = "Direttiva" if a["typ"] == "dir" else "Regolamento"
        data["acts"][a["key"]] = dict(
            label=f"{tname} (UE) 2024/{a['num']}",
            short=a["short"], file=page_for(a["key"]),
            articles=arts_data, recitals=rct_data)

    print("Generazione pagine…")
    nav = " ".join(
        f'<a href="{page_for(x["key"])}" title="{x["title"]}">'
        f'<span class="nav-kw">{x["nav"]}</span> {x["num"]}</a>' for x in ACTS)
    for a in ACTS:
        toc = build_toc(a)
        (OUT / page_for(a["key"])).write_text(page_html(a, toc, nav, version=VERSION), encoding="utf-8")
    (OUT / "index.html").write_text(index_html(reg, version=VERSION), encoding="utf-8")
    (OUT / "assets" / "data.js").write_text(
        "window.PACTO=" + json.dumps(data, ensure_ascii=False) + ";window.PACTO_V=" + json.dumps(VERSION) + ";", encoding="utf-8")

    print("Generazione pagine atti esterni…")
    (OUT / "assets" / "data-ext").mkdir(exist_ok=True)
    for key, ext in EXT_BY_KEY.items():
        (OUT / ext["page"]).write_text(ext_page_html(ext, nav, version=VERSION),
                                       encoding="utf-8")
        ext_data = dict(label=ext["label"], short=ext["short"], file=ext["page"],
                        external=True, version=ext["version"], eurlex=ext["eurlex"],
                        articles=ext_extract_frags(ext), recitals={})
        (OUT / "assets" / "data-ext" / f"{key}.js").write_text(
            f'window.PACTO.acts[{json.dumps(key)}]=' +
            json.dumps(ext_data, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"  {len(EXT_BY_KEY)} pagine esterne generate")
    (OUT / "audit.html").write_text(audit_html(), encoding="utf-8")

    # validazione: ogni href interno deve puntare a un'ancora esistente
    print("Validazione ancore…")
    ids = {}
    for a in ACTS:
        s = {el.get("id") for el in a["container"].find_all(id=True)}
        for anx in a["anx_els"]:
            s.add(anx.get("id"))
            s |= {el.get("id") for el in anx.find_all(id=True)}
        ids[page_for(a["key"])] = s
    for key, ext in EXT_BY_KEY.items():
        s = set()
        for c in ext["containers"]:
            if isinstance(c, Tag):
                if c.get("id"):
                    s.add(c["id"])
                s |= {el.get("id") for el in c.find_all(id=True)}
        ids[ext["page"]] = s
    broken = 0
    for a in ACTS:
        links = a["container"].find_all("a", class_="xref")
        for anx in a["anx_els"]:
            links += anx.find_all("a", class_="xref")
        for link in links:
            href = link.get("href", "")
            if href.startswith("http"):
                continue
            if "#" in href:
                page, frag = href.split("#", 1)
                page = page or page_for(a["key"])
                if frag not in ids.get(page, set()):
                    broken += 1
                    print(f"  ROTTO: {a['key']} → {href}")
    print(f"Ancore rotte: {broken}")
    print(f"Issues in audit: {len(AUDIT.issues)}")
    print("Fatto. Output in:", OUT)


if __name__ == "__main__":
    main()
