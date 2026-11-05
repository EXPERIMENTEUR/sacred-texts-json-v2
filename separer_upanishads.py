# -*- coding: ascii -*-
"""Upanishads : reperage PRUDENT du commentaire de Max Mueller melange au texte.
Ne modifie pas le champ "text". Ajoute a chaque fichier :
  "commentaire_traducteur" : paragraphes de commentaire (exclus de l'analyse)
  "bruit"                  : en-tetes de page / debris (exclus)
A lancer dans le dossier sacred-texts-json. Peut etre relance sans risque."""
import json, os, re

DOSSIER = "upanishads"
NUM = re.compile(r"^[\(\[]?\s*\d+\s*[\.\)\]]|^[\(\[]?[IVXL]+[\.\)]\s")
VOIX = re.compile(
    r"(commentator|\bComm\.|Professor|\bProf\.|Sankara|\bAnkara\b|Sa[ml]kar|Mah.?dhara|\bUvata\b|"
    r"\bCowell\b|\bWeber\b|Colebrooke|\bRoer\b|Rammohun|\bPoley\b|Vijn.?n|V\\f|\xc2nandagiri|\bAnandagiri\b|"
    r"[Tt]he translator|\bI think\b|\bI hold\b|seems to me|text is (?:very )?corrupt|\bMSS?\.|commentary|our translation)")

def paras(texte):
    t = texte.replace("__NOTOC__", "")
    t = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", t)
    t = re.sub(r"={2,}[^=\n]*={2,}", "", t)
    t = re.sub(r"'{2,}", "", t)
    return [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", t) if p.strip()]

def classe(nom, texte):
    ps = paras(texte)
    dernier = None
    if nom == "Isa_Vagasaneyi":
        cand = [i for i, p in enumerate(ps) if re.match(r"^18\.", p)]
        dernier = cand[-1] if cand else None
    com, bruit = [], []
    for i, p in enumerate(ps):
        if p in ("Footnotes", "Layout 2") or re.match(r"^\d+Sacred Books of the East", p) or re.fullmatch(r"[\W_]*", p):
            bruit.append(p)
        elif dernier is not None and i > dernier:
            com.append(p)
        elif not NUM.match(p) and VOIX.search(p) and len(p.split()) >= 12:
            com.append(p)
    return com, bruit

for fn in sorted(os.listdir(DOSSIER)):
    if not fn.endswith(".json"):
        continue
    chemin = os.path.join(DOSSIER, fn)
    with open(chemin, "r", encoding="utf-8-sig") as f:
        d = json.load(f)
    com, bruit = classe(fn[:-5], d.get("text", ""))
    d["commentaire_traducteur"] = com
    d["bruit"] = bruit
    with open(chemin, "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, ensure_ascii=False, indent=4)
    print("%-22s %4d paragraphes de commentaire (%5d mots) | %2d de bruit | %4d notes de bas de page" % (
        fn[:-5], len(com), sum(len(p.split()) for p in com), len(bruit), len(d.get("notes", []))))
