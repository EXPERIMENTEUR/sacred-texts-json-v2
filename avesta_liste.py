import requests

headers = {"User-Agent": "TelechargementPersonnel/1.0 (usage prive; contact: jerom_yapo@outlook.fr)"}
api = "https://en.wikisource.org/w/api.php"

for volume in (4, 23, 31):
    prefixe = f"Sacred Books of the East/Volume {volume}/"
    params = {"action": "query", "list": "allpages", "apprefix": prefixe, "aplimit": "500", "format": "json"}
    r = requests.get(api, params=params, headers=headers)
    pages = [p["title"] for p in r.json()["query"]["allpages"]]
    print(f"Volume {volume} : {len(pages)} sous-pages")
    for titre in pages[:60]:
        print("   ", titre)