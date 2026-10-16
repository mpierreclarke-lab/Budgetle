# Budgetle

Jeu de devinette inspiré de Tradle : retrouver un pays européen à partir de ses dépenses publiques.
Données préparées à l'avance, règles déterministes, page statique, aucune IA pendant les parties.

## Reproduire les données

```
python3 scripts/01_download.py        # données brutes Eurostat + centroïdes (data/raw, avec .meta.json : URL, date, SHA-256)
python3 scripts/02_build_profiles.py  # data/derived/profils_2024.{json,csv}, metadata.json, controles_2024.txt
npm install && node scripts/04_simulate.mjs   # vérifie geo.js contre geolib, simule les règles
python3 scripts/05_build_site.py      # site/dist/regles.html (page autonome)
node scripts/05_check_site.mjs        # vérifie les données affichées et les affirmations des notes
```

## Choix arrêtés (séance 2)

| Sujet | Choix |
|---|---|
| Périmètre | S13 (toutes APU), consolidé, dépense totale TE |
| Pays / année | 30 pays (UE-27 + IS, NO, CH), 2024 |
| Indice principal | dépense totale en % du PIB |
| Catégories | 10 divisions COFOG en % du PIB et en euros ; protection sociale détaillée en 7 sous-catégories |
| Surfaces du treemap | parts dans la dépense totale, calculées à partir des millions d'euros |
| Proximité | géographique avec boussole, formule et code de Tradle ; échelle européenne (4 778 km) à confirmer |
| Essais | 6 |

## Arborescence

- `data/raw/` : fichiers bruts tels que téléchargés (ne jamais éditer à la main)
- `data/derived/` : tables prêtes pour le jeu et rapports de contrôle
- `docs/comparabilite.md` : fiches pays et limites de comparabilité
- `site/js/` : logique du jeu (distance, direction, treemap), testée
- `site/src/` → `site/dist/` : page de règles

Données © Union européenne, Eurostat (réutilisation avec mention de la source). Mécanique géographique : Tradle (MIT).
