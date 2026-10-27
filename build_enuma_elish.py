# -*- coding: utf-8 -*-
# Construit enuma_elish_complete.json a partir de enuma_gutenberg.txt
# (Project Gutenberg #9914, "The Babylonian Legends of the Creation", British Museum, 1921).
import re, json, sys, io

SRC = "enuma_gutenberg.txt"
OUT = "enuma_elish_complete.json"

raw = io.open(SRC, encoding="utf-8-sig", errors="replace").read().replace("\r", "")
a = raw.index("THE SEVEN TABLETS OF CREATION.--TRANSLATION.")
b = raw.index("\nNOTES.\n", a)
body = raw[a:b].split("\n", 1)[1]

# paragraphes
paras = [re.sub(r"\s*\n\s*", " ", p).strip() for p in re.split(r"\n\s*\n", body)]
paras = [p for p in paras if p]

# regroupe les crochets ouverts non fermes (notes et illustrations sur plusieurs paragraphes)
merged, cur = [], None
for p in paras:
    if cur is not None:
        cur += " " + p
        if cur.count("[") <= cur.count("]"):
            merged.append(cur); cur = None
        continue
    if p.startswith("[") and p.count("[") > p.count("]"):
        cur = p
        continue
    merged.append(p)
if cur is not None:
    merged.append(cur)

NUMS = ["FIRST", "SECOND", "THIRD", "FOURTH", "FIFTH", "SIXTH", "SEVENTH"]
head_re = re.compile(r"^(%s) TABLET\.?(\s*\[\d+\])?$" % "|".join(NUMS))
tablets, tab, last = [], None, None
mark = re.compile(r"\s*\[\d+\]")

for p in merged:
    m = head_re.match(p)
    if m:
        tab = {"tablet": NUMS.index(m.group(1)) + 1, "title": m.group(1).capitalize() + " Tablet",
               "lines": [], "notes": []}
        tablets.append(tab); last = None
        continue
    if tab is None:
        continue
    if p.startswith("[Illustration"):
        continue
    if p == "EPILOGUE.":
        tab["lines"].append({"kind": "titre", "text": "Epilogue"}); last = None
        continue
    mf = re.match(r"^\[Footnote \d+:\s*(.*)\]$", p)
    if mf:
        note = mf.group(1).strip()
        if last is not None:
            last.setdefault("notes", []).append(note)
        else:
            tab["notes"].append(note)
        continue
    if p.startswith("[Line"):
        tab["lines"].append({"kind": "lacune", "text": p.strip("[]").strip()}); last = None
        continue
    ml = re.match(r"^(\d+)\.\s+(.*)$", p)
    if ml:
        e = {"n": int(ml.group(1)), "text": mark.sub("", ml.group(2)).strip()}
        tab["lines"].append(e); last = e
        continue
    # reste : resume de l'editeur (pas du texte antique)
    tab["lines"].append({"kind": "resume_editeur", "text": mark.sub("", p)}); last = None

data = {
    "work": "Enuma Elish (The Seven Tablets of Creation)",
    "edition": "The Babylonian Legends of the Creation and the Fight between Bel and the Dragon, British Museum, 1921 (text by E. A. Wallis Budge), Project Gutenberg #9914",
    "license": "Public domain (1921). Project Gutenberg edition.",
    "note": "Traduction anglaise ancienne, tres lacunaire : les crochets [ ] marquent des restitutions, '...' des lacunes. Les entrees 'resume_editeur' sont des resumes de l'editeur moderne, pas du texte antique ; 'lacune' signale des vers non traduits.",
    "tablets": tablets,
}
io.open(OUT, "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False, indent=1))

print("Fichier:", OUT)
for t in tablets:
    L = [x for x in t["lines"] if "n" in x]
    nums = [x["n"] for x in L]
    gaps = [(nums[i], nums[i+1]) for i in range(len(nums)-1) if nums[i+1] != nums[i] + 1]
    print("%-15s vers=%3d  1er=%s dernier=%s  lacunes=%d  resumes=%d  notes=%d  sauts=%s" % (
        t["title"], len(L), nums[:1], nums[-1:],
        sum(1 for x in t["lines"] if x.get("kind") == "lacune"),
        sum(1 for x in t["lines"] if x.get("kind") == "resume_editeur"),
        len(t["notes"]) + sum(len(x.get("notes", [])) for x in L), gaps[:8]))