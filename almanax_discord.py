#!/usr/bin/env python3
"""
Envoie sur un webhook Discord la liste des ressources à acheter
pour faire l'Almanax du mois suivant (Dofus 3), pour 1 et 4 personnages.

Source des données : API dofusdu.de (gratuite, sans clé).
Aucune dépendance externe : Python 3.8+ suffit.

Usage :
    python3 almanax_discord.py              # mois suivant
    python3 almanax_discord.py 2026-12      # mois précis (pour tester)
    python3 almanax_discord.py --dry-run    # affiche sans envoyer
"""

import json
import os
import sys
import calendar
import urllib.request
from collections import OrderedDict
from datetime import date

# ======================= CONFIG =======================
# Sur GitHub : secret DISCORD_WEBHOOK_URL. En local : variable d'env ou colle l'URL ici.
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")
NB_PERSOS = [1, 4]          # colonnes de quantités à afficher
LANG = "fr"
GAME = "dofus3"             # "dofus3" (Unity) ou "dofus2"
# ======================================================

API = f"https://api.dofusdu.de/{GAME}/v1/{LANG}/almanax"
MOIS_FR = ["", "janvier", "février", "mars", "avril", "mai", "juin", "juillet",
           "août", "septembre", "octobre", "novembre", "décembre"]
HEADERS = {"User-Agent": "almanax-discord-script/1.0"}


def mois_cible(argv):
    for a in argv:
        if len(a) == 7 and a[4] == "-":
            return int(a[:4]), int(a[5:])
    today = date.today()
    return (today.year + 1, 1) if today.month == 12 else (today.year, today.month + 1)


def fetch_almanax(year, month):
    last = calendar.monthrange(year, month)[1]
    url = (f"{API}?range%5Bfrom%5D={year}-{month:02d}-01"
           f"&range%5Bto%5D={year}-{month:02d}-{last:02d}")
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def regrouper(jours):
    """Additionne les quantités quand un même objet revient plusieurs jours."""
    items = OrderedDict()
    for j in sorted(jours, key=lambda d: d["date"]):
        trib = j["tribute"]
        nom = trib["item"]["name"]
        it = items.setdefault(nom, {"qte": 0, "jours": [], "type": trib["item"].get("subtype", "")})
        it["qte"] += trib["quantity"]
        it["jours"].append(int(j["date"][8:10]))
    return items


def construire_embeds(year, month, jours, items):
    titre = f"📅 Almanax de {MOIS_FR[month]} {year}"
    kamas = sum(j.get("reward_kamas", 0) for j in jours)

    # --- Liste de courses (regroupée) ---
    entete = " / ".join(f"{n} perso{'s' if n > 1 else ''}" for n in NB_PERSOS)
    lignes = []
    for nom, it in sorted(items.items(), key=lambda kv: kv[0].lower()):
        qtes = " / ".join(f"**{it['qte'] * n}**" for n in NB_PERSOS)
        equip = " 🛡️" if it["type"] == "equipment" else ""
        lignes.append(f"• {nom}{equip} — {qtes}")

    courses = (f"Quantités : {entete}\n"
               f"{len(items)} objets différents sur {len(jours)} jours.\n"
               f"Kamas gagnés (1 perso) : **{kamas:,}**\n\n".replace(",", " ")
               + "\n".join(lignes))

    # --- Détail jour par jour ---
    detail = "\n".join(
        f"`{j['date'][8:10]}` {j['tribute']['item']['name']} ×{j['tribute']['quantity']}"
        for j in sorted(jours, key=lambda d: d["date"])
    )

    embeds = []
    for i, bloc in enumerate(decouper(courses, 4000)):
        embeds.append({"title": titre if i == 0 else None,
                       "description": bloc, "color": 0xE8A33D})
    for i, bloc in enumerate(decouper(detail, 4000)):
        embeds.append({"title": "Détail par jour" if i == 0 else None,
                       "description": bloc, "color": 0x5865F2})
    return [{k: v for k, v in e.items() if v is not None} for e in embeds]


def decouper(texte, limite):
    """Discord limite une description d'embed à 4096 caractères."""
    blocs, courant = [], ""
    for ligne in texte.split("\n"):
        if len(courant) + len(ligne) + 1 > limite:
            blocs.append(courant)
            courant = ""
        courant += ligne + "\n"
    if courant.strip():
        blocs.append(courant)
    return blocs


def envoyer(embeds):
    # Discord : max 10 embeds et 6000 caractères par message -> un message par embed
    for e in embeds:
        data = json.dumps({"username": "Almanax", "embeds": [e]}).encode()
        req = urllib.request.Request(
            WEBHOOK_URL, data=data,
            headers={**HEADERS, "Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=30).close()


def main():
    year, month = mois_cible(sys.argv[1:])
    jours = fetch_almanax(year, month)
    items = regrouper(jours)
    embeds = construire_embeds(year, month, jours, items)

    if "--dry-run" in sys.argv:
        for e in embeds:
            print(f"\n=== {e.get('title', '')} ===\n{e['description']}")
    else:
        if not WEBHOOK_URL:
            sys.exit("Erreur : DISCORD_WEBHOOK_URL n'est pas défini.")
        envoyer(embeds)
        print(f"Envoyé : almanax {month:02d}/{year}, {len(items)} objets.")


if __name__ == "__main__":
    main()
