# -*- coding: utf-8 -*-
"""Estrae il testo del regolamento rimpatri (P10_TA(2026)0207, IT) dall'HTML
del Parlamento europeo in markdown pulito, stesso formato dei file KB in
TESTI MD/RAG-cleaned/ (paragrafi separati da riga vuota, considerando come
"| (N)\n| testo", note a piè di pagina come [(N)] + elenco finale)."""
import re, sys
from bs4 import BeautifulSoup

SRC = sys.argv[1]
OUT = sys.argv[2]

html = open(SRC, encoding="utf-8").read()
# Isola la sezione "title2" (posizione del PE = testo del regolamento)
start = html.find('<a name="title2">')
soup = BeautifulSoup(html[start:], "lxml")

def clean(s: str) -> str:
    s = s.replace("▮", "").replace("▌", "")      # marcatori di soppressione
    s = s.replace("\xa0", " ").replace(" ", " ").replace("\t", " ")
    s = re.sub(r" {4,}", "   ", s)
    s = re.sub(r"[ ]+([,;.)])", r"\1", s)
    return s.strip()

lines = []

# Titolo del documento (riga doc_title)
title_td = soup.find("tr", class_="doc_title")
if title_td:
    lines.append(clean(title_td.get_text(" ", strip=True)))

footnote_texts = {}   # n -> testo
footnote_tables = set()

# Le note finali stanno in una tabella con anchor name="def_2_N":
# individua la tabella PIÙ INTERNA che contiene ciascuna nota
for a in soup.find_all("a", attrs={"name": re.compile(r"^def_2_\d+$")}):
    n = a["name"].split("_")[-1]
    row = a.find_parent("tr")
    if row:
        tds = row.find_all("td")
        if len(tds) >= 2:
            footnote_texts[n] = clean(tds[-1].get_text(" ", strip=True))
        footnote_tables.add(id(a.find_parent("table")))

# Corpo: tutti i <p> in ordine di documento, esclusi quelli nella tabella note
body_paras = []
for p in soup.find_all("p"):
    t = p.find_parent("table")
    if t is not None and id(t) in footnote_tables:
        continue
    body_paras.append(p)

def render_paragraph(p) -> str:
    # sostituisce i richiami di nota <a href="#def_2_N">(N)</a> con [(N)]
    for a in p.find_all("a", href=re.compile(r"#def_2_\d+")):
        n = a["href"].split("_")[-1]
        a.replace_with(f"[({n})]")
    return clean(p.get_text(" ", strip=True))

for p in body_paras:
    txt = render_paragraph(p)
    if not txt:
        continue
    # considerando: "(12)  testo" / "(2 bis)  testo" -> formato tabella KB
    m = re.match(r"^\((\d+(?:\s+\w+)?)\)\s+(.*)$", txt)
    if m and len(m.group(2)) > 40:
        lines.append(f"| ({m.group(1)})\n| {m.group(2)}")
        continue
    lines.append(txt)

# de-duplica il sommario iniziale (il titolo compare due volte)
out = "\n\n".join(lines)

if footnote_texts:
    notes = "\n\n".join(
        f"[({n})] {t}" for n, t in sorted(footnote_texts.items(), key=lambda kv: int(kv[0]))
    )
    out += "\n\n---\n\nNOTE\n\n" + notes

open(OUT, "w", encoding="utf-8").write(out + "\n")
print("scritto", OUT, len(out), "caratteri,", len(footnote_texts), "note")
