#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Construit pistis_sophia_complete.json a partir de pistis_gutenberg.txt.

Source : Pistis Sophia, traduction litterale du copte par George Horner (1924),
introduction de Francis Legge. Project Gutenberg #76266 (domaine public).

Ce qui est garde : les quatre Documents (traduction), paragraphe par paragraphe.
Ce qui est exclu : l'introduction de Legge, l'index des psaumes, l'index general,
les notes de transcription. Les notes de l'editeur sur les lacunes sont gardees
mais marquees kind = "note_editeur" (a ne pas analyser comme texte).
Les numeros de feuillets [12^a] sont retires du texte et conserves dans "folios".
"""
import json
import re
import sys

SRC = "pistis_gutenberg.txt"
OUT = "pistis_sophia_complete.json"

RE_DOC = re.compile(r"^\s{10,}THE (FIRST|SECOND|THIRD|FOURTH) DOCUMENT\s*$")
RE_FIN = re.compile(r"^\s{10,}INDEX OF PSALMS AND ODES\s*$")
RE_FOLIO = re.compile(r"\[(\d+)\^([ab])\]")
RE_ORN = re.compile(r"^[\s*]+$")


def main():
    with open(SRC, encoding="utf-8") as f:
        lignes = f.read().replace("\r", "").split("\n")

    debut = [i for i, l in enumerate(lignes) if RE_DOC.match(l)]
    fin = [i for i, l in enumerate(lignes) if RE_FIN.match(l)]
    if len(debut) != 4 or len(fin) != 1:
        print("ERREUR: structure inattendue", len(debut), len(fin))
        sys.exit(1)
    bornes = debut + [fin[0]]

    noms = {"FIRST": "Premier", "SECOND": "Deuxieme",
            "THIRD": "Troisieme", "FOURTH": "Quatrieme"}
    documents = []
    for k in range(4):
        a, b = bornes[k], bornes[k + 1]
        cle = RE_DOC.match(lignes[a]).group(1)
        # blocs separes par lignes vides
        blocs, cur = [], []
        for l in lignes[a:b]:
            if l.strip() == "":
                if cur:
                    blocs.append(cur)
                    cur = []
            else:
                cur.append(l)
        if cur:
            blocs.append(cur)

        # en-tete : premiers blocs fortement indentes
        entete = []
        while blocs and all(re.match(r"^\s{10,}\S", l) for l in blocs[0]):
            entete.extend(x.strip() for x in blocs.pop(0))
        titre = entete[0]
        sous = [re.sub(r"[_\[\]]", "", x) for x in entete[1:]]

        paragraphes = []
        n = 0
        i = 0
        while i < len(blocs):
            bloc = blocs[i]
            i += 1
            brut = " ".join(x.strip() for x in bloc)
            brut = re.sub(r"(\u2014)\s+", r"\1", brut)  # tiret cadratin en fin de ligne
            if RE_ORN.match(brut):
                continue
            kind = "texte"
            if bloc[0].startswith("Footnote "):
                suite = ""
                if i < len(blocs):
                    suite = " ".join(x.strip() for x in blocs[i])
                    i += 1
                brut = bloc[0].strip().rstrip(":") + " : " + suite
                kind = "note_editeur"
            elif (brut.startswith("[") and brut.endswith("]")
                  and not RE_FOLIO.match(brut)) or \
                 re.match(r"^\(_.*_\)$", brut):
                kind = "note_editeur"
            folios = ["%s%s" % (m.group(1), m.group(2))
                      for m in RE_FOLIO.finditer(brut)]
            t = RE_FOLIO.sub(" ", brut)
            t = re.sub(r"\[\d+\]", "", t)          # renvoi de note
            t = t.replace("_", "")                 # italiques Gutenberg
            t = re.sub(r"\s+", " ", t).strip()
            t = re.sub(r"\s+([,.;:!?)])", r"\1", t)
            t = re.sub(r"\(\s+", "(", t)
            if not t:
                continue
            n += 1
            p = {"n": n, "kind": kind, "text": t}
            if folios:
                p["folios"] = folios
            paragraphes.append(p)

        documents.append({
            "id": k + 1,
            "title": "The %s Document" % cle.capitalize(),
            "title_fr": "%s Document" % noms[cle],
            "subtitle": " ".join(sous),
            "paragraphs": paragraphes,
        })

    data = {
        "title": "Pistis Sophia",
        "translator": "George Horner",
        "edition": "SPCK, Londres, 1924 (Project Gutenberg #76266)",
        "note": ("Traduction litterale du copte (codex Askew). Les mots entre "
                 "parentheses sont des ajouts ou variantes du traducteur. "
                 "Les paragraphes kind=note_editeur sont des notes de "
                 "l'editeur (lacunes, ornements), pas du texte."),
        "documents": documents,
    }
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    tot_p = tot_m = 0
    for d in documents:
        ps = [p for p in d["paragraphs"] if p["kind"] == "texte"]
        nn = len(d["paragraphs"]) - len(ps)
        mots = sum(len(p["text"].split()) for p in ps)
        tot_p += len(ps)
        tot_m += mots
        print("Document %d : %d paragraphes, %d notes editeur, %d mots"
              % (d["id"], len(ps), nn, mots))
    print("TOTAL : %d paragraphes, %d mots" % (tot_p, tot_m))


if __name__ == "__main__":
    main()
