# telecharge_testaments.py - Testament des 12 Patriarches (Wikisource, ANF vol. VIII)
# Lecture seule via l'API officielle MediaWiki. Reprenable : saute les pages deja telechargees.
import requests, json, os, time, re

PREFIXE = "Ante-Nicene Fathers/Volume VIII/The Testaments of the Twelve Patriarchs/"
API = "https://en.wikisource.org/w/api.php"
HEADERS = {"User-Agent": "SacredTextsPersonalProject/1.0 (etude privee; python-requests)"}
DOSSIER = "testaments_sources"
PAUSE = 8  # secondes entre deux pages
os.makedirs(DOSSIER, exist_ok=True)

def demande(params):
    for essai in range(6):
        r = requests.get(API, params=params, headers=HEADERS, timeout=30)
        if r.status_code == 429:
            attente = int(r.headers.get("Retry-After", "60")) + 5
            print("  Wikisource demande de ralentir : attente de", attente, "secondes...")
            time.sleep(attente)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError("Trop de refus 429, reessayez plus tard.")

titres, suite = [], {}
while True:
    data = demande({"action": "query", "list": "allpages", "apprefix": PREFIXE,
                    "aplimit": 100, "format": "json", **suite})
    titres += [p["title"] for p in data["query"]["allpages"]]
    if "continue" in data:
        suite = data["continue"]; time.sleep(PAUSE)
    else:
        break
print("Sous-pages trouvees :", len(titres))

rapport = []
for t in titres:
    court = t.replace(PREFIXE, "")
    nom = re.sub(r"[^A-Za-z0-9]+", "_", court).strip("_")[:60] or "page"
    chemin = os.path.join(DOSSIER, nom + ".json")
    if os.path.exists(chemin):
        with open(chemin, "r", encoding="utf-8") as f:
            rapport.append((court, len(json.load(f)["wikitext"]), "deja la"))
        continue
    d = demande({"action": "parse", "page": t, "prop": "wikitext", "format": "json"})
    if "error" in d:
        print("ECHEC", court, d["error"].get("info")); continue
    wt = d["parse"]["wikitext"]["*"]
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump({"title": t, "source": "https://en.wikisource.org/wiki/" + t.replace(" ", "_"),
                   "wikitext": wt}, f, ensure_ascii=False, indent=1)
    print("OK", court[:60])
    rapport.append((court, len(wt), "telecharge"))
    time.sleep(PAUSE)

print()
print("Pages disponibles :", len(rapport), "sur", len(titres))
for court, n, etat in rapport:
    print("  %-62s %7d  %s" % (court[:62], n, etat))