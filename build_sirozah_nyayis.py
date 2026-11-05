# -*- coding: ascii -*-
"""Sirozahs et Nyayishes (Darmesteter 1883, SBE vol. 23) : construit sirozah_nyayis_darmesteter.json
a partir des pages sbe2304, sbe2305 (Sirozahs) et sbe2330..sbe2334 (Nyayishes).
Separe : texte / intro_traducteur / notes. Usage : python build_sirozah_nyayis.py [sbe23_html] [sortie.json]"""
import html, json, os, re, sys

DOSSIER = sys.argv[1] if len(sys.argv) > 1 else "sbe23_html"
SORTIE = sys.argv[2] if len(sys.argv) > 2 else "sirozah_nyayis_darmesteter.json"

def lire(n):
    with open(os.path.join(DOSSIER, "sbe23%02d.htm" % n), "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def nettoie(h):
    h = re.sub(r"<A NAME=\"page_\d+\">.*?</A>", " ", h, flags=re.I | re.S)
    h = re.sub(r"<A NAME=\"fr_\d+\"></A>\s*<A HREF=\"#fn_\d+\">.*?</A>", "", h, flags=re.I | re.S)
    h = re.sub(r"<A NAME=\"img_\d+\"></A>\s*<IMG[^>]*>", "[?]", h, flags=re.I | re.S)
    h = re.sub(r"\[paragraph continues\]", " ", h)
    h = re.sub(r"<br\s*/?>", " ", h, flags=re.I)
    h = re.sub(r"<[^>]+>", "", h)
    h = html.unescape(h).replace(chr(0xa0), " ")
    h = re.sub(r"\s+", " ", h).strip()
    return re.sub(r"\s+([,.;:!?])", r"\1", h)

RX_BLOC = re.compile(r"<(h[1-4]|p)[^>]*>(.*?)</\1>", re.I | re.S)
RX_FN = re.compile(r"<P><A NAME=\"fn_(\d+)\"></A><A HREF=\"[^\"]*\">([^<]*)</A>(.*?)</P>", re.I | re.S)
RX_PAGE = re.compile(r"^(?:p\. \d+\s*)+$")
RX_DIV = re.compile(r"^_{5,}$")
RX_JOUR = re.compile(r"^(\d+)\.\s*(.*?)\.?$")
RX_VERS = re.compile(r"^\[?(\d+)\s*\.\s+")

def blocs_page(n):
    s = lire(n)
    corps = s.split('<A NAME="fn_')[0]
    out = []
    for m in RX_BLOC.finditer(corps):
        t = nettoie(m.group(2))
        if not t or RX_PAGE.match(t) or t.startswith("The Zend Avesta, Part II") or t == "Footnotes":
            continue
        out.append((m.group(1).lower(), t))
    notes = [{"ref": nettoie(m.group(2)), "text": nettoie(m.group(3))} for m in RX_FN.finditer(s)]
    return out, notes

NOMS_JOURS = {6: "Khord\u00e2d"}   # titre absent de la source (jour 6)

sirozahs = []
for k, n in enumerate((4, 5), 1):
    blocs, notes = blocs_page(n)
    titre, jours = "?", []
    for tag, t in blocs:
        if tag == "h3":
            titre = t
        elif tag == "h4":
            m = RX_JOUR.match(t)
            num = int(m.group(1)) if m else None
            if jours and num and jours[-1]["n"] and num == jours[-1]["n"] + 2 and len(jours[-1]["paras"]) > 1 and (jours[-1]["n"] + 1) in NOMS_JOURS:
                # heading manquant dans la source : le dernier paragraphe du jour precedent est le jour manquant
                manquant = jours[-1]["paras"].pop()
                jours.append({"n": jours[-1]["n"] + 1, "nom": NOMS_JOURS[jours[-1]["n"] + 1], "paras": [manquant], "restitue": True})
            jours.append({"n": num, "nom": m.group(2) if m else t, "paras": []})
        elif jours:
            jours[-1]["paras"].append(t)
    for j in jours:
        j["text"] = " ".join(j.pop("paras")).strip()
    sirozahs.append({"id": k, "titre": titre, "source": "sbe23%02d.htm" % n, "jours": jours, "notes": notes})

nyayis = []
for k, n in enumerate(range(30, 35), 1):
    blocs, notes = blocs_page(n)
    titre, paras, phase = "?", [], "texte"
    h1 = [t for tag, t in blocs if tag in ("h1", "h3")]
    if any(tag == "h1" for tag, t in blocs):
        phase = "intro"          # page 30 : intro generale puis ____ puis I. KHORSHED NYAYIS
    for tag, t in blocs:
        if tag == "h1":
            continue
        if tag == "h3":
            titre = t
            phase = "texte"
            continue
        if RX_DIV.match(t):
            phase = "texte"
            continue
        if phase == "intro":
            paras.append({"kind": "intro_traducteur", "text": t})
            continue
        mv = RX_VERS.match(t)
        if mv:
            paras.append({"kind": "texte", "n": int(mv.group(1)), "text": t[mv.end():].strip()})
        else:
            paras.append({"kind": "texte", "n": None, "text": t})
    nyayis.append({"id": k, "titre": titre, "source": "sbe23%02d.htm" % n, "paragraphs": paras, "notes": notes})

out = {
    "title": "Sirozahs et Nyayishes (Zend Avesta, Part II)",
    "translator": "James Darmesteter (1883), Sacred Books of the East vol. 23",
    "note": "sirozahs : 30 jours chacun (texte). nyayis : kind=texte traduction (les '. . . .' sont des abreviations de Darmesteter pour des formules repetees) ; intro_traducteur : introduction generale (exclue de l'analyse) ; notes : notes de bas de page (exclues).",
    "sirozahs": sirozahs,
    "nyayis": nyayis,
}
with open(SORTIE, "w", encoding="utf-8", newline="\n") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

def asc(x):
    return x.encode("ascii", "replace").decode()
tot = 0
for s in sirozahs:
    mots = sum(len(j["text"].split()) for j in s["jours"])
    tot += mots
    vides = [j["n"] for j in s["jours"] if not j["text"]]
    print("Sirozah %d : %2d jours, %5d mots, notes %3d, jours vides %s, numeros %s" % (
        s["id"], len(s["jours"]), mots, len(s["notes"]), vides, [j["n"] for j in s["jours"]] == list(range(1, 31))))
for y in nyayis:
    mt = sum(len(p["text"].split()) for p in y["paragraphs"] if p["kind"] == "texte")
    mi = sum(len(p["text"].split()) for p in y["paragraphs"] if p["kind"] == "intro_traducteur")
    tot += mt
    print("Nyayis %d %-22s paragraphes %3d texte %4d mots intro %3d notes %2d" % (
        y["id"], asc(y["titre"])[:22], len(y["paragraphs"]), mt, mi, len(y["notes"])))
print("TOTAL texte :", tot, "mots")
