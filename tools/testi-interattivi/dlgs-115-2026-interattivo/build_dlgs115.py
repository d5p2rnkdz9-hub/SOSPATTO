#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build the interactive text of d.lgs. 12 giugno 2026, n. 115 (attuazione della direttiva (UE)
2024/1712, che modifica la direttiva 2011/36/UE sulla tratta di esseri umani; G.U. n. 150 del
1° luglio 2026, in vigore dal 16 luglio 2026).

Like the d.l. 100/2026 it is a decree that amends other acts by novella — among them art. 18
d.lgs. 286/1998 (art. 8), art. 17 d.lgs. 142/2015 and art. 32 d.lgs. 25/2008 (art. 11), whose
coordinated texts show those changes — so it REUSES build_dl100.py as-is (GU-typography parser,
per-comma novella targets, renderer), only swapping source, identity and page template.

SOURCE: Normattiva caricaArticolo HTML in ../nm_fresh_20260929/dlgs115/ (14 articles, snapshot of
29 September 2026, fetch_normattiva.py --act dlgs115). Registered in ../sites.json as
'dlgs-2026-115' (slug dlgs-115-2026), so the sibling builders link «decreto legislativo 12 giugno
2026, n. 115» here hoverably.
"""
import os, importlib.util, io, contextlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')

_spec = importlib.util.spec_from_file_location('dl100', os.path.join(ROOT, 'dl-100-2026-interattivo', 'build_dl100.py'))
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)
E = B.E

B.HERE = HERE
B.SRC = os.path.join(ROOT, 'nm_fresh_20260929', 'dlgs115')
E.SELF_KEY = 'dlgs-2026-115'
E.SELF_IT = tuple(E.SITES['acts'][E.SELF_KEY]['it'])        # ('decreto.legislativo', '115')
E.KNOWN_DATE[('decreto.legislativo', '115')] = '2026-06-12'
B.SELF_LABEL = 'D.Lgs. 12 giugno 2026, n. 115'
B.SELF_SHORT = 'D.Lgs. 115/2026'
B.CAPI = []

B.PAGE_TMPL = """<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>D.Lgs. 115/2026 (tratta di esseri umani) — testo vigente interattivo</title>
<link rel="stylesheet" href="assets/style.css">
<link rel="stylesheet" href="assets/amend.css">
</head>
<body data-act="dlgs-2026-115">
<header class="topbar">
  <a class="home" href="../index.html">&#8962; Patto UE</a> <a class="home-here" href="#top">D.Lgs. 115/2026</a>
  <button id="toc-toggle">Sommario</button>
  <span class="topttl">Attuazione della direttiva (UE) 2024/1712 sulla tratta — <b>testo vigente</b>, rinvii normativi navigabili</span>
</header>
<div class="amd-banner">Testo del <b>decreto legislativo 12 giugno 2026, n. 115</b> (G.U. Serie generale n. 150 del 1° luglio 2026, in vigore dal 16 luglio 2026), di attuazione della direttiva (UE) 2024/1712, che modifica la direttiva 2011/36/UE sulla prevenzione e la repressione della tratta di esseri umani e la protezione delle vittime. Tra le altre, modifica per novella l'art. 18 del <a href="../dlgs-286-1998/index.html#art_18">d.lgs. 286/1998</a> (art. 8), l'art. 17 del <a href="../dlgs-142-2015/index.html#art_17">d.lgs. 142/2015</a> e l'art. 32 del <a href="../dlgs-25-2008/index.html#art_32">d.lgs. 25/2008</a> (art. 11): nei rispettivi testi coordinati se ne leggono la versione precedente e le modifiche. Ogni rinvio normativo è navigabile.</div>
<div class="layout">
<nav class="toc" id="toc"><div class="toc-title">D.Lgs. 12 giugno 2026, n. 115</div>
{toc}
</nav>
<main class="doc" id="top">
<div class="eli-main-title"><p class="oj-doc-ti">DECRETO LEGISLATIVO 12 giugno 2026, n. 115</p>
<p class="oj-doc-ti sub">Attuazione della direttiva (UE) 2024/1712 del Parlamento europeo e del Consiglio, del 13 giugno 2024, che modifica la direttiva 2011/36/UE concernente la prevenzione e la repressione della tratta di esseri umani e la protezione delle vittime</p>
<p class="oj-doc-ti note">Testo vigente — rinvii normativi navigabili</p></div>
{body}
<p class="disclaimer">Testo non ufficiale a fini di studio. Fonte: Normattiva / Gazzetta Ufficiale Serie generale n. 150 del 1° luglio 2026 (cod. red. 26G00130). Fa fede unicamente il testo pubblicato nella Gazzetta Ufficiale.</p>
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
