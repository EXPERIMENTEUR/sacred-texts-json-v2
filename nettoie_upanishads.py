# nettoie_upanishads.py - separe, dans les Upanishads de Wikisource, le texte (traduction de Max Mueller)
# des elements de navigation (retires) et des notes de bas de page de Mueller (gardees dans le champ "notes").
# Sauvegarde les fichiers avant nettoyage dans upanishads_brut/. Peut etre relance sans risque.
import json, os, re, shutil

NOMS = ["Khandogya", "Kena_Talavakara", "Isa_Vagasaneyi", "Katha", "Mundaka", "Prasna"]
os.makedirs("upanishads_brut", exist_ok=True)

def nettoyer_page(chunk):
    lignes = chunk.split("\n")
    debut = 0
    for i, l in enumerate(lignes[:25]):
        if re.match(r"^\d+Sacred Books of the East Volume \d+", l.strip()):
            debut = i + 1
    if debut == 0:
        for i, l in enumerate(lignes[:25]):
            if l.strip() in ("\u2190", "\u2192") or "translated by Friedrich Max" in l:
                debut = i + 1
    lignes = lignes[debut:]
    fin = next((i for i, l in enumerate(lignes) if l.lstrip().startswith("\u2191")), len(lignes))
    corps = "\n".join(lignes[:fin]).strip()
    notes = [l.lstrip("\u2191 ").strip() for l in lignes[fin:] if l.strip()]
    return corps, notes

for nom in NOMS:
    chemin = os.path.join("upanishads", nom + ".json")
    d = json.load(open(chemin, encoding="utf-8"))
    if "notes" in d:
        print("deja nettoye :", nom); continue
    shutil.copyfile(chemin, os.path.join("upanishads_brut", nom + ".json"))
    pages = re.split(r"\n\n(?=\u2190\n)", d["text"])
    corps, notes = [], []
    for p in pages:
        c, n = nettoyer_page(p)
        if c: corps.append(c)
        notes += n
    d["text"] = "\n\n".join(corps)
    d["notes"] = notes
    json.dump(d, open(chemin, "w", encoding="utf-8"), ensure_ascii=False, indent=4)
    print("%-16s texte %7d car. | %4d notes de Mueller (%d car.)" % (nom, len(d["text"]), len(notes), sum(map(len, notes))))