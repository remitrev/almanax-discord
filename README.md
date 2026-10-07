# Almanax → Discord

Chaque mois, le 25, prépare la liste des objets à acheter pour l'Almanax du mois suivant (quantités pour 1 et 4 personnages) :

- une **page web** avec, pour chaque objet, un bouton **Copier** et une **case à cocher** (mémorisée dans ton navigateur) ;
- un **message Discord** qui résume la liste et donne le lien vers la page.

Données : [API dofusdu.de](https://api.dofusdu.de).

## Installation

1. **Secret Discord** : Settings → Secrets and variables → Actions → New repository secret
   - Nom : `DISCORD_WEBHOOK_URL`
   - Valeur : l'URL du webhook Discord
2. **GitHub Pages** : Settings → Pages → *Build and deployment*
   - Source : **Deploy from a branch**
   - Branche : **main**, dossier **/docs** → Save
   - Avec un compte GitHub gratuit, Pages exige un dépôt **public**. Le webhook reste protégé dans les secrets.
3. Onglet **Actions** → *Almanax du mois suivant* → **Run workflow** pour tester.

## Choisir une période

Dans **Run workflow** :
- **Date de début** / **Date de fin** au format `2026-10-07`
- seulement le début : jusqu'à la fin du mois
- rien : le mois suivant complet

Chaque période a sa propre page (`docs/AAAA-MM-JJ_AAAA-MM-JJ.html`), et `docs/index.html` contient toujours la dernière.

## Réglages

En haut de `almanax_discord.py` :
- `NB_PERSOS = [1, 4]` : quantités proposées
- `GAME = "dofus3"` : ou `"dofus2"`
- `LOGOS` : emojis par type d'objet

Date d'envoi : ligne `cron` dans `.github/workflows/almanax.yml` (heure UTC).

## En local

```
python3 almanax_discord.py --dry-run                     # génère la page, n'envoie rien
python3 almanax_discord.py 2026-10-07 2026-10-31 --dry-run
```
