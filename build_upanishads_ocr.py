# build_upanishads_ocr.py - Kaushitaki, Taittiriya, Brihadaranyaka, Svetasvatara, Maitrayana
# a partir du texte OCR (Google/archive.org) de "The Upanishads" de Max Mueller (SBE vol. 1 et 15, 1879/1884).
# Le texte de Mueller et ses notes de bas de page sont separes (champs "text" et "notes").
import html, json, os, re

SRC = "upanishads_ocr.txt"
brut = open(SRC, encoding="utf-8", errors="replace").read()
m = re.search(r"<pre>(.*?)</pre>", brut, re.S)
lines = html.unescape(m.group(1) if m else brut).splitlines()

def trouver(motif, debut=0, fin=None):
    rx = re.compile(motif)
    for i in range(debut, fin if fin else len(lines)):
        if rx.search(lines[i]):
            return i
    return None

# --- bornes de chaque Upanishad (ancres sur les titres imprimes) ---
k0 = trouver(r"^KAUSHITAKI-UPANISHAD\.\s*$", 15000)
k1 = trouver(r"^VAGASANEYI-SA.{1,4}HITA-\s*$", k0)
t0 = trouver(r"^TAITTIRIYAKA-UPANISHAD\.\s*$", k1)
b0 = trouver(r"^B.{0,6}HADARA.{0,6}KA-\s*$", t0)
s0 = trouver(r"^\S{0,3}VETA\S{0,4}VATARA-\s*$", b0)
p0 = trouver(r"^PRA.{1,4}A-UPANISHAD\.", s0)
a0 = trouver(r"^MAITRAYA.{1,5}-BRAHMA.{1,4}-\s*$", p0)
a1 = trouver(r"^TRANSLITERATION\s+OF\s+ORIENTAL", a0)
BORNES = {"Kaushitaki": (k0, k1), "Taittiriya": (t0, b0), "Brihadaranyaka": (b0, s0),
          "Svetasvatara": (s0, p0), "Maitrayana": (a0, a1)}
print("Bornes :", {k: v for k, v in BORNES.items()})

ORD = r"(?:First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth|Eleventh|Twelfth)"
RE_TITRE_SECT = re.compile(r"^(?:%s|[A-Z]+TH|FIRST|SECOND|THIRD|FOURTH|FIFTH|SIXTH|SEVENTH|EIGHTH)\s+\S{3,}" % ORD, re.I)
RE_NOTE = re.compile(r"^[\^\*'\"\u2022\u00b0\u00bb\u2020\u2021\u00a7`~\-\u2014]{1,2}\s+\S")

def majuscule(s):
    L = [c for c in s if c.isalpha()]
    return bool(L) and sum(c.isupper() for c in L) / len(L)

def entete(s):
    """En-tete de page : majuscules + chiffre (ex. '46 TAITTIRIYAKA-UPANISHAD.', 'I ADHYAYA, 3 BRAHMANA, 27. 83')."""
    return len(s) <= 80 and majuscule(s) >= 0.55 and bool(re.search(r"\d", s)) and not re.match(r"^\d{1,3}\.\s", s)

def titre_imprime(s):
    return len(s) <= 60 and majuscule(s) >= 0.6 and re.search(r"UPAN|BRAH|ARAJV|HADARA|VETA", s) and not re.search(r"\d", s)

def numero(s):
    m = re.match(r"^(\d{1,3})\s?[.,]\s", s)
    if m:
        return int(m.group(1))
    if re.match(r"^[Ii1l]\s?\.\s", s):
        return 1
    return None

def joindre(ls):
    t = ""
    for x in ls:
        x = x.strip()
        t = (t[:-1] + x) if (t.endswith("-") and x[:1].islower()) else (t + " " + x).strip()
    return re.sub(r"\s+", " ", t)

def traiter(deb, fin):
    paras, cur = [], []
    for l in lines[deb:fin] + [""]:
        if l.strip():
            cur.append(l)
        elif cur:
            paras.append(cur); cur = []
    texte, notes = [], []
    mode, last_v = "texte", 0
    for p in paras:
        premiere = p[0].strip()
        if len(p) == 1 and entete(premiere):
            mode = "texte"; continue
        if all(titre_imprime(x.strip()) or re.fullmatch(r"U\s?PAN\s?I\s?SHAD\W*", x.strip()) or not x.strip() for x in p):
            continue
        p = [x for x in p if not entete(x.strip())] or p
        premiere = p[0].strip()
        n = numero(premiere)
        est_titre_sect = len(p) <= 2 and bool(RE_TITRE_SECT.match(premiere)) and len(premiere) < 45
        if mode == "texte":
            if RE_NOTE.match(premiere) and n is None:
                mode = "notes"; notes.append(joindre(p)); continue
            if n:
                last_v = n
            texte.append(joindre(p))
        else:
            if est_titre_sect or (n is not None and (n == 1 or last_v < n <= last_v + 2)):
                mode = "texte"
                if n:
                    last_v = n
                texte.append(joindre(p))
            else:
                notes.append(joindre(p))
    # raccord des pages : un paragraphe qui commence en minuscule prolonge le precedent si celui-ci est reste ouvert ;
    # sinon c'est la suite d'une note de bas de page commencee sur la page precedente
    final = []
    for t in texte:
        if t[:1].islower() and final:
            fin_prec = final[-1].rstrip(" \"'*^)]\u2019\u201d")[-1:]
            if fin_prec in ".?!;:":
                notes.append(t); continue
            final[-1] = final[-1] + " " + t; continue
        final.append(t)
    return final, notes

os.makedirs("upanishads", exist_ok=True)
for nom, (deb, fin) in BORNES.items():
    texte, notes = traiter(deb, fin)
    d = {"name": nom,
         "source": "https://archive.org/details/upanishads00mlgoog (F. Max Mueller, The Upanishads, SBE vol. 1 et 15 ; texte issu d'un OCR : signes diacritiques abimes)",
         "text": "\n\n".join(texte), "notes": notes}
    json.dump(d, open(os.path.join("upanishads", nom + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=4)
    print("%-15s lignes %5d-%5d | texte %7d car. | %4d notes (%d car.)" % (nom, deb, fin, len(d["text"]), len(notes), sum(map(len, notes))))