# -*- coding: utf-8 -*-
"""Scarica i testi italiani degli atti esterni citati nel Patto dal repository
CELLAR dell'Ufficio delle pubblicazioni (EUR-Lex è dietro WAF).
Preferisce la versione consolidata più recente (scoperta via SPARQL);
ripiega sul testo GU originale. Output: "Atti esterni html/" + manifest.json
"""
import json
import re
import subprocess
import time
from pathlib import Path

BASE = Path(__file__).parent
OUT = BASE / "Atti esterni html"
OUT.mkdir(exist_ok=True)

CELEX_LETTER = {"reg": "R", "reg_impl": "R", "reg_del": "R",
                "dir": "L", "dir_impl": "L", "dir_del": "L",
                "dec": "D", "dec_impl": "D", "dec_framw": "F"}

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/17.0 Safari/605.1.15")


def curl(url, *hdrs, timeout=60):
    cmd = ["curl", "-s", "-L", "--compressed", "--max-time", str(timeout), "-A", UA]
    for h in hdrs:
        cmd += ["-H", h]
    cmd.append(url)
    r = subprocess.run(cmd, capture_output=True)
    return r.stdout.decode("utf-8", errors="replace")


def latest_consolidated(celex):
    q = ('PREFIX cdm: <http://publications.europa.eu/ontology/cdm#> '
         'SELECT ?c WHERE { ?w cdm:resource_legal_id_celex ?c . '
         f'FILTER(STRSTARTS(STR(?c), "0{celex[1:]}-")) }}')
    out = subprocess.run(
        ["curl", "-s", "-G", "http://publications.europa.eu/webapi/rdf/sparql",
         "--data-urlencode", "query=" + q, "-H", "Accept: text/csv", "-A", UA,
         "--max-time", "40"],
        capture_output=True).stdout.decode("utf-8", errors="replace")
    dates = re.findall(r"-(\d{8})", out)
    return max(dates) if dates else None


def fetch_cellar(celex_id):
    html = curl(f"http://publications.europa.eu/resource/celex/{celex_id}",
                "Accept: application/xhtml+xml", "Accept-Language: ita")
    if len(html) > 15000 and "Articolo" in html:
        return html
    return None


def main():
    acts = json.load(open(BASE / "ext_acts.json"))
    mpath = OUT / "manifest.json"
    manifest = json.load(open(mpath)) if mpath.exists() else {}
    ok = fail = skip = 0
    for a in acts:
        key = f"{a['t']}-{a['year']}-{a['num']}"
        fp = OUT / f"{key}.html"
        if fp.exists() and manifest.get(key, {}).get("version"):
            skip += 1
            continue
        letter = CELEX_LETTER[a["t"]]
        celex = f"3{a['year']}{letter}{a['num']:04d}"
        html, version = None, None
        try:
            date = latest_consolidated(celex)
        except Exception:
            date = None
        if date:
            html = fetch_cellar(f"0{celex[1:]}-{date}")
            if html:
                version = f"consolidato {date[:4]}-{date[4:6]}-{date[6:]}"
        if not html:
            html = fetch_cellar(celex)
            if html:
                version = "originale GU"
        if html:
            fp.write_text(html, encoding="utf-8")
            manifest[key] = {"t": a["t"], "year": a["year"], "num": a["num"],
                             "cites": a["cites"], "version": version, "celex": celex,
                             "bytes": len(html)}
            ok += 1
            print(f"OK   {key:22s} {version:28s} {len(html)//1024} KB", flush=True)
        else:
            manifest[key] = {"t": a["t"], "year": a["year"], "num": a["num"],
                             "cites": a["cites"], "error": "nessun XHTML in CELLAR",
                             "celex": celex}
            fail += 1
            print(f"FAIL {key:22s} nessun XHTML in CELLAR", flush=True)
        json.dump(manifest, open(mpath, "w"), indent=1, ensure_ascii=False)
        time.sleep(0.4)
    print(f"\nScaricati: {ok}, falliti: {fail}, già presenti: {skip}", flush=True)


if __name__ == "__main__":
    main()
