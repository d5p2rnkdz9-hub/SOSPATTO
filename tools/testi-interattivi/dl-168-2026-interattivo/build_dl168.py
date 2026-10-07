#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build the interactive text of d.l. 29 settembre 2026, n. 168 (misure urgenti in materia di
giustizia, di funzionalità del Ministero dell'interno e di impianti di interesse strategico
nazionale; G.U. n. 226 del 29 settembre 2026, in vigore dal 30 settembre 2026, in conversione).

For the Pact only art. 4 matters: it amends by novella art. 17 of d.l. 100/2026 (transitional
competence of questure and border police extended to 30 April 2027; validity and effects of the
document issued at registration). The d.l. 100 page shows that change as the layer
amendments_dl168.json. Like build_dlgs115.py, it REUSES build_dl100.py as-is.

SOURCE: Normattiva caricaArticolo HTML in ../nm_fresh_20261006/dl168/ (7 articles, snapshot of
6 October 2026, fetch_normattiva.py --act dl168). Registered in ../sites.json as 'dl-2026-168'
(slug dl-168-2026).
"""
import os, importlib.util, io, contextlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')

_spec = importlib.util.spec_from_file_location('dl100', os.path.join(ROOT, 'dl-100-2026-interattivo', 'build_dl100.py'))
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)
E = B.E

B.HERE = HERE
B.SRC = os.path.join(ROOT, 'nm_fresh_20261006', 'dl168')
E.SELF_KEY = 'dl-2026-168'
E.SELF_IT = tuple(E.SITES['acts'][E.SELF_KEY]['it'])        # ('decreto.legge', '168')
E.KNOWN_DATE[('decreto.legge', '168')] = '2026-09-29'
B.SELF_LABEL = 'D.L. 29 settembre 2026, n. 168'
B.SELF_SHORT = 'D.L. 168/2026'
B.CAPI = []

B.PAGE_TMPL = """<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>D.L. 168/2026 (regime transitorio del Patto) — testo vigente interattivo</title>
<link rel="stylesheet" href="assets/style.css">
<link rel="stylesheet" href="assets/amend.css">
</head>
<body data-act="dl-2026-168">
<header class="topbar">
  <a class="home" href="../index.html">&#8962; Patto UE</a> <a class="home-here" href="#top">D.L. 168/2026</a>
  <button id="toc-toggle">Sommario</button>
  <span class="topttl">Giustizia, Ministero dell'interno, regime transitorio del Patto — <b>testo vigente</b>, rinvii normativi navigabili</span>
</header>
<div class="amd-banner">Testo del <b>decreto-legge 29 settembre 2026, n. 168</b> (G.U. Serie generale n. 226 del 29 settembre 2026, in vigore dal 30 settembre 2026, <b>in corso di conversione</b>). Per il Patto rileva l'art. 4, che modifica per novella l'art. 17 del <a href="../dl-100-2026/index.html#art_17">d.l. 100/2026</a>: proroga al <b>30 aprile 2027</b> la competenza transitoria di questure e uffici di polizia di frontiera a ricevere manifestazione, registrazione e formalizzazione della domanda (comma 1) e stabilisce che il documento rilasciato alla registrazione equivale a quello dell'art. 4, comma 4, del <a href="../dlgs-142-2015/index.html#art_4">d.lgs. 142/2015</a>, vale un anno dalla registrazione, salvo rinnovo, e consente il lavoro ai sensi dell'art. 22, comma 1 (comma 3). Nel testo del d.l. 100 se ne leggono la versione precedente e le modifiche. Ogni rinvio normativo è navigabile.</div>
<div class="layout">
<nav class="toc" id="toc"><div class="toc-title">D.L. 29 settembre 2026, n. 168</div>
{toc}
</nav>
<main class="doc" id="top">
<div class="eli-main-title"><p class="oj-doc-ti">DECRETO-LEGGE 29 settembre 2026, n. 168</p>
<p class="oj-doc-ti sub">Misure urgenti in materia di giustizia, di funzionalità del Ministero dell'interno e di impianti di interesse strategico nazionale</p>
<p class="oj-doc-ti note">Testo vigente — rinvii normativi navigabili</p></div>
{body}
<p class="disclaimer">Testo non ufficiale a fini di studio. Fonte: Normattiva / Gazzetta Ufficiale Serie generale n. 226 del 29 settembre 2026 (cod. red. 26G00188). Fa fede unicamente il testo pubblicato nella Gazzetta Ufficiale.</p>
</main>
</div>
<div id="tip" class="tip" hidden></div>
<aside id="panel" class="panel" hidden>
  <div class="panel-bar"><button id="panel-back" class="pbtn" hidden>&#8592;</button><div id="panel-crumb" class="crumb"></div><button id="panel-close" class="pbtn">&#10005;</button></div>
  <div id="panel-body" class="panel-body"></div>
  <div class="panel-foot"><a class="panel-home" href="../index.html">&#8962; Patto UE</a><a id="panel-go" href="#">Vai all'articolo &#8594;</a></div>
</aside>
<button id="return-chip" hidden>&#8617; Torna al punto precedente</button>
<script src="assets/data.js"></script>
<script src="assets/app.js"></script>
</body>
</html>"""

if __name__ == '__main__':
    B.main()
