# telecharge_upanishads.py - repare les Upanishads de Wikisource (SBE vol. 1 et 15). Lecture seule, API officielle.
# Lit liste_upanishads.json (deja cree). Sauvegarde les anciens fichiers dans upanishads_old/.
import requests, json, os, time, re, html, unicodedata, shutil

API = "https://en.wikisource.org/w/api.php"
HEADERS = {"User-Agent": "SacredTextsPersonalProject/1.0 (etude privee; python-requests)"}
PAUSE = 8

def sans_accent(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).lower()

def demande(params):
    for essai in range(6):
        r = requests.get(API, params=params, headers=HEADERS, timeout=30)
        if r.status_code == 429:
            time.sleep(int(r.headers.get("Retry-After", "60")) + 5); continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError("Trop de refus 429, reessayez plus tard.")

def en_texte(h):
    h = re.sub(r"(?is)<(script|style)\b.*?</\1>", "", h)
    h = re.sub(r"(?is)<sup\b.*?</sup>", "", h)
    h = re.sub(r'(?is)<span[^>]*class="[^"]*(pagenum|ws-noexport|mw-editsection)[^"]*"[^>]*>.*?</span>', "", h)
    h = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</li>|</h\d>|</tr>", "\n", h)
    h = re.sub(r"(?s)<[^>]+>", "", h)
    h = html.unescape(h)
    h = re.sub(r"[ \t\u00a0]+", " ", h)
    h = re.sub(r"\n\s*\n+", "\n\n", h)
    return h.strip()

liste = json.load(open("liste_upanishads.json", encoding="utf-8"))
titres = liste["Sacred Books of the East/Volume 1/"] + liste["Sacred Books of the East/Volume 15/"]

# nom du fichier -> mot-cle du titre principal
CIBLES = {"Khandogya": "khandogya-upanishad", "Kena_Talavakara": "talavakara-upanishad",
          "Isa_Vagasaneyi": "vagasaneyi-samhita-upanishad", "Katha": "katha-upanishad",
          "Mundaka": "mundaka-upanishad", "Prasna": "prasna-upanishad"}

os.makedirs("upanishads", exist_ok=True)
os.makedirs("upanishads_old", exist_ok=True)
os.makedirs("upanishads_sources", exist_ok=True)

for nom, cle in CIBLES.items():
    principal = next((t for t in titres if sans_accent(t.split("/")[-1]) == cle), None)
    if not principal:
        print("INTROUVABLE :", nom); continue
    pages = [principal] + sorted([t for t in titres if t.startswith(principal + "/")],
                                 key=lambda t: ["first","second","third","fourth","fifth","sixth","seventh","eighth"].index(sans_accent(t.split("/")[-1]).split()[0]) if sans_accent(t.split("/")[-1]).split()[0] in ["first","second","third","fourth","fifth","sixth","seventh","eighth"] else 99)
    morceaux = []
    for t in pages:
        d = demande({"action": "parse", "page": t, "prop": "text", "format": "json", "disablelimitreport": 1})
        if "error" in d:
            print("ECHEC", t, d["error"].get("info")); continue
        h = d["parse"]["text"]["*"]
        open(os.path.join("upanishads_sources", re.sub(r"[^A-Za-z0-9]+", "_", t)[:80] + ".html"), "w", encoding="utf-8").write(h)
        txt = en_texte(h)
        print("  %-60s %7d car." % (t.split("Sacred Books of the East/")[-1][:60], len(txt)))
        morceaux.append(txt)
        time.sleep(PAUSE)
    texte = "\n\n".join(morceaux)
    chemin = os.path.join("upanishads", nom + ".json")
    if os.path.exists(chemin):
        shutil.copyfile(chemin, os.path.join("upanishads_old", nom + ".json"))
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump({"name": nom, "source": "https://en.wikisource.org/wiki/" + principal.replace(" ", "_"), "text": texte},
                  f, ensure_ascii=False, indent=4)
    print("==>", nom, ":", len(texte), "caracteres\n")