# Almanax → Discord

Chaque mois, le 25, poste sur un webhook Discord la liste des ressources à acheter pour faire l'Almanax du mois suivant, avec les quantités pour 1 et 4 personnages.

Données : [API dofusdu.de](https://api.dofusdu.de).

## Installation

1. Dans le dépôt : **Settings → Secrets and variables → Actions → New repository secret**
   - Nom : `DISCORD_WEBHOOK_URL`
   - Valeur : l'URL du webhook Discord
2. Onglet **Actions** → *Almanax du mois suivant* → **Run workflow** pour tester tout de suite.

Ensuite, ça tourne tout seul le 25 de chaque mois.

## Réglages

En haut de `almanax_discord.py` :
- `NB_PERSOS = [1, 4]` : colonnes de quantités
- `GAME = "dofus3"` : ou `"dofus2"`

Date d'envoi : ligne `cron` dans `.github/workflows/almanax.yml` (heure UTC).

## En local

```
python3 almanax_discord.py --dry-run          # affiche sans envoyer
python3 almanax_discord.py 2026-12 --dry-run  # un mois précis
```
