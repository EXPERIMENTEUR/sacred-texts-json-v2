# -*- coding: ascii -*-
"""Yashts (Darmesteter 1883, SBE vol. 23) : construit yashts_darmesteter.json
a partir des pages HTML sbe2306..sbe2329. Separe : texte / formule / intro_traducteur / notes."""
import html, json, os, re, sys

DOSSIER = sys.argv[1] if len(sys.argv) > 1 else "sbe23_html"
SORTIE = sys.argv[2] if len(sys.argv) > 2 else "yashts_darmesteter.json"

def lire(p):
    with open(p, "r", encoding="utf-8", errors="replace") as f:
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

RX_P = re.compile(r"<p[^>]*>(.*?)</p>", re.I | re.S)
RX_H = re.compile(r"<h[1-4][^>]*>(.*?)</h[1-4]>", re.I | re.S)
RX_FN = re.compile(r"<P><A NAME=\"fn_(\d+)\"></A><A HREF=\"[^\"]*\">([^<]*)</A>(.*?)</P>", re.I | re.S)
RX_VERS = re.compile(r"^\[?(\d+)((?:,\s*\d+)*)\.?\s*(?:\(([^)]*)\)\.?)?\s")
RX_DIV = re.compile(r"^_{5,}$")

yashts = []
for n in range(6, 30):
    nom = "sbe23%02d.htm" % n
    s = lire(os.path.join(DOSSIER, nom))
    corps = s.split('<A NAME="fn_')[0]
    titres = [nettoie(h) for h in RX_H.findall(corps)]
    titres = [t for t in titres if t and t != "Footnotes"]
    titre = next((t for t in titres if "YA" in t.upper() and "T" in t.upper()), titres[0] if titres else "?")
    # paragraphes avec marque "dans un bloc FONT -1" (le bloc peut s'etendre sur plusieurs <p>)
    blocs, dans_font = [], False
    for pm in RX_P.finditer(corps):
        brut = pm.group(1)
        brut_t = re.sub(r"<A NAME=\"fr_\d+\"></A>\s*<A HREF=\"#fn_\d+\">.*?</A>", "", brut, flags=re.I | re.S)
        if re.search(r'<FONT SIZE="?-1"?', brut_t, re.I):
            dans_font = True
        t = nettoie(brut)
        if re.search(r"</FONT>", brut_t, re.I) and not re.search(r'<FONT SIZE="?-1"?', brut_t, re.I):
            est_font = True
            dans_font = False
        else:
            est_font = dans_font
            if re.search(r"</FONT>", brut_t, re.I):
                dans_font = False
        if t and not t.startswith("The Zend Avesta, Part II"):
            blocs.append((t, est_font))
    paras = []
    phase = "intro"
    for t, est_font in blocs:
        if RX_DIV.match(t):
            phase = "formule"
            continue
        mv = RX_VERS.match(t + " ") if len(t) > 12 else None
        premier = bool(re.match(r"^\[?1(?:\s*\(\d+\))?\.?\s", t)) and not est_font
        if phase != "texte" and premier:
            phase = "texte"
        if phase == "texte":
            prec = [p["n"] for p in paras if p["kind"] == "texte" and p["n"]]
            if mv:
                num = int(mv.group(1))
                erreur = bool(prec) and (num < prec[-1] or num > prec[-1] + 5)
                fin = re.findall(r"\d+", mv.group(2) or "")
                paras.append({"kind": "texte", "n": prec[-1] + 1 if erreur else num,
                              "n_fin": int(fin[-1]) if fin else None, "n_alt": mv.group(3),
                              "n_imprime": num if erreur else None, "text": t[mv.end() - 1:].strip()})
            elif paras and paras[-1]["kind"] == "texte":
                paras[-1]["text"] += " " + t
            else:
                paras.append({"kind": "texte", "n": None, "text": t})
        elif phase == "formule":
            paras.append({"kind": "formule", "text": t})
        else:
            paras.append({"kind": "intro_traducteur", "text": t})
    notes = [{"ref": nettoie(m.group(2)), "text": nettoie(m.group(3))} for m in RX_FN.finditer(s)]
    yashts.append({"id": len(yashts) + 1, "titre": titre, "source": nom, "paragraphs": paras, "notes": notes})

out = {
    "title": "The Yashts (Zend Avesta, Part II)",
    "translator": "James Darmesteter (1883), Sacred Books of the East vol. 23",
    "note": "kind=texte : traduction ; formule : formule d'ouverture/fermeture traduite ; intro_traducteur : resume/commentaire de Darmesteter (exclu de l'analyse) ; notes : notes de bas de page (exclues).",
    "yashts": yashts,
}
with open(SORTIE, "w", encoding="utf-8", newline="\n") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
tt = ti = nn = 0
for y in yashts:
    mw = lambda k: sum(len(p["text"].split()) for p in y["paragraphs"] if p["kind"] == k)
    vs = [p for p in y["paragraphs"] if p["kind"] == "texte"]
    tt += mw("texte"); ti += mw("intro_traducteur"); nn += len(y["notes"])
    print("%2d %-40s verses %3d texte %5d formule %4d intro %4d notes %3d" % (
        y["id"], y["titre"][:40].encode("ascii", "replace").decode(), len(vs), mw("texte"), mw("formule"), mw("intro_traducteur"), len(y["notes"])))
print("TOTAL : texte %d mots, intro %d mots, %d notes" % (tt, ti, nn))
