#!/usr/bin/env python3
"""
Envoie sur un webhook Discord la liste des ressources à acheter
pour faire l'Almanax sur une période (Dofus 3), pour 1 et 4 personnages.
Génère aussi une page web (docs/) avec, pour chaque objet, un bouton
« Copier » et une case à cocher. Le message Discord contient le lien.

Source des données : API dofusdu.de (gratuite, sans clé).
Aucune dépendance externe : Python 3.8+ suffit.

Usage :
    python3 almanax_discord.py                          # mois suivant complet
    python3 almanax_discord.py 2026-12                  # un mois précis
    python3 almanax_discord.py 2026-10-07 2026-10-31    # du 7 au 31 octobre
    python3 almanax_discord.py 2026-10-07               # du 7 à la fin du mois
    ... --dry-run                                        # affiche sans envoyer
                                                         # (la page est quand même générée)
"""

import json
import os
import sys
import calendar
import urllib.request
from collections import OrderedDict
from datetime import date, timedelta

from page import generer_page

# ======================= CONFIG =======================
# Sur GitHub : secret DISCORD_WEBHOOK_URL. En local : variable d'env ou colle l'URL ici.
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")
NB_PERSOS = [1, 4]          # quantités affichées
# Adresse de la page web (GitHub Pages). Déduite automatiquement sur GitHub.
_REPO = os.environ.get("GITHUB_REPOSITORY", "remitrev/almanax-discord")
PAGE_BASE = os.environ.get("PAGE_BASE", f"https://{_REPO.split('/')[0]}.github.io/{_REPO.split('/')[1]}/")
DOSSIER_PAGES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
LANG = "fr"
GAME = "dofus3"             # "dofus3" (Unity) ou "dofus2"
# ======================================================

API = f"https://api.dofusdu.de/{GAME}/v1/{LANG}/almanax"
MOIS_FR = ["", "janvier", "février", "mars", "avril", "mai", "juin", "juillet",
           "août", "septembre", "octobre", "novembre", "décembre"]
HEADERS = {"User-Agent": "almanax-discord-script/1.1"}
LIMITE_EMBED = 4000         # Discord : 4096 caractères max par description

# Logo affiché devant chaque objet selon son type (champ "subtype" de l'API)
LOGOS = {
    "resources": ("🌿", "ressource"),
    "equipment": ("⚔️", "équipement"),
    "consumables": ("🧪", "consommable"),
}
LOGO_INCONNU = ("❔", "autre")


def logo(subtype):
    return LOGOS.get(subtype, LOGO_INCONNU)[0]


def fin_de_mois(d):
    return d.replace(day=calendar.monthrange(d.year, d.month)[1])


def periode(args):
    """Renvoie (debut, fin) selon les arguments, par défaut le mois suivant."""
    dates = [a for a in args if not a.startswith("--") and a.strip()]
    if not dates:
        prochain = (date.today().replace(day=1) + timedelta(days=32)).replace(day=1)
        return prochain, fin_de_mois(prochain)
    if len(dates[0]) == 7:                       # AAAA-MM
        debut = date.fromisoformat(dates[0] + "-01")
        return debut, fin_de_mois(debut)
    debut = date.fromisoformat(dates[0])
    fin = date.fromisoformat(dates[1]) if len(dates) > 1 else fin_de_mois(debut)
    if fin < debut:
        sys.exit("Erreur : la date de fin est avant la date de début.")
    return debut, fin


def fetch_almanax(debut, fin):
    url = f"{API}?range%5Bfrom%5D={debut.isoformat()}&range%5Bto%5D={fin.isoformat()}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return sorted(json.load(r), key=lambda d: d["date"])


def regrouper(jours):
    """Additionne les quantités quand un même objet revient plusieurs jours."""
    items = OrderedDict()
    for j in jours:
        trib = j["tribute"]
        nom = trib["item"]["name"]
        it = items.setdefault(nom, {"qte": 0, "type": trib["item"].get("subtype", ""),
                                    "icone": trib["item"].get("image_urls", {}).get("icon", "")})
        it["qte"] += trib["quantity"]
    return items


def libelle_periode(debut, fin):
    if debut.day == 1 and fin == fin_de_mois(debut):
        return f"de {MOIS_FR[debut.month]} {debut.year}"
    d = f"{debut.day} {MOIS_FR[debut.month]}"
    if debut.year != fin.year:
        d += f" {debut.year}"
    elif debut.month == fin.month:
        d = f"{debut.day}"
    return f"du {d} au {fin.day} {MOIS_FR[fin.month]} {fin.year}"


def regrouper_en_blocs(morceaux, limite):
    """Assemble des morceaux de texte en blocs sans jamais couper un morceau."""
    blocs, courant = [], ""
    for m in morceaux:
        if courant and len(courant) + len(m) + 1 > limite:
            blocs.append(courant)
            courant = ""
        courant += m + "\n"
    if courant.strip():
        blocs.append(courant)
    return blocs


def construire_embeds(debut, fin, jours, items, url_page):
    titre = f"📅 Almanax {libelle_periode(debut, fin)}"
    kamas = sum(j.get("reward_kamas", 0) for j in jours)
    persos = " / ".join(f"{n} perso{'s' if n > 1 else ''}" for n in NB_PERSOS)

    entete = (f"### [👉 Ouvrir la liste à cocher]({url_page})\n"
              f"Bouton copier + case à cocher pour chaque objet.\n\n"
              f"{len(items)} objets sur {len(jours)} jours · "
              f"{kamas:,} kamas gagnés par perso\n".replace(",", " ")
              + "Quantités : " + persos + " · "
              + " · ".join(f"{e} {t}" for e, t in LOGOS.values()) + "\n")

    morceaux = [entete]
    for nom, it in sorted(items.items(), key=lambda kv: kv[0].lower()):
        qtes = " / ".join(f"**{it['qte'] * n}**" for n in NB_PERSOS)
        morceaux.append(f"{logo(it['type'])} {nom} — {qtes}")

    embeds = []
    for i, bloc in enumerate(regrouper_en_blocs(morceaux, LIMITE_EMBED)):
        e = {"description": bloc, "color": 0xE8A33D}
        if i == 0:
            e["title"] = titre
            e["url"] = url_page
        embeds.append(e)
    return embeds


def ecrire_pages(debut, fin, jours, items):
    """Écrit docs/<debut>_<fin>.html (lien permanent) et docs/index.html (dernière liste)."""
    os.makedirs(DOSSIER_PAGES, exist_ok=True)
    titre = f"Almanax {libelle_periode(debut, fin)}"
    html = generer_page(titre, debut, fin, jours, items, NB_PERSOS, LOGOS)
    nom = f"{debut.isoformat()}_{fin.isoformat()}.html"
    for f in (nom, "index.html"):
        with open(os.path.join(DOSSIER_PAGES, f), "w", encoding="utf-8") as fh:
            fh.write(html)
    # .nojekyll : GitHub Pages sert les fichiers tels quels
    open(os.path.join(DOSSIER_PAGES, ".nojekyll"), "w").close()
    return PAGE_BASE + nom


def poster(payload):
    data = json.dumps({"username": "Almanax", **payload}).encode()
    req = urllib.request.Request(
        WEBHOOK_URL, data=data,
        headers={**HEADERS, "Content-Type": "application/json"}, method="POST")
    urllib.request.urlopen(req, timeout=30).close()


def envoyer(embeds):
    # Discord : 6000 caractères max par message -> un message par embed
    for e in embeds:
        poster({"embeds": [e]})


def main():
    args = sys.argv[1:]
    debut, fin = periode(args)
    jours = fetch_almanax(debut, fin)
    items = regrouper(jours)
    url_page = ecrire_pages(debut, fin, jours, items)
    embeds = construire_embeds(debut, fin, jours, items, url_page)

    if "--dry-run" in args:
        for e in embeds:
            print(f"\n=== {e.get('title', '')} ===\n{e['description']}")
        print(f"\nPage : {url_page}")
    else:
        if not WEBHOOK_URL:
            sys.exit("Erreur : DISCORD_WEBHOOK_URL n'est pas défini.")
        envoyer(embeds)
        print(f"Envoyé : almanax du {debut} au {fin}, {len(items)} objets.")


if __name__ == "__main__":
    main()
