# Budgetle

Jeu de devinette inspiré de Tradle : retrouver un pays européen à partir de ses dépenses publiques.
Données préparées à l'avance, règles déterministes, page statique, aucune IA pendant les parties.

## Reproduire les données

```
python3 scripts/01_download.py        # données brutes Eurostat + centroïdes (data/raw, avec .meta.json : URL, date, SHA-256)
python3 scripts/02_build_profiles.py  # data/derived/profils_2024.{json,csv}, metadata.json, controles_2024.txt
npm install && node scripts/04_simulate.mjs   # vérifie geo.js contre geolib, simule les règles
python3 scripts/06_build_calendar.py  # data/derived/calendrier.json (pays du jour, 360 jours)
python3 scripts/05_build_site.py      # site/dist/index.html (jeu) et regles.html, pages autonomes
node scripts/05_check_site.mjs        # vérifie les données affichées et les affirmations des notes
node scripts/07_test_game.mjs         # tests de la logique de partie et du calendrier
python3 scripts/08_e2e.py             # partie complète jouée dans un navigateur (Playwright)
```

## Choix arrêtés (séance 2)

| Sujet | Choix |
|---|---|
| Périmètre | S13 (toutes APU), consolidé, dépense totale TE |
| Pays / année | 30 pays (UE-27 + IS, NO, CH), 2024 |
| Indice principal | montant total des dépenses en euros, puis (entre parenthèses) en % du PIB |
| Catégories | 10 divisions COFOG en % du PIB et en euros ; protection sociale détaillée en 7 sous-catégories |
| Surfaces du treemap | parts dans la dépense totale, calculées à partir des millions d'euros |
| Proximité | géographique avec boussole, formule et code de Tradle ; échelle européenne (4 778 km) |
| Essais | 6 |
| Pays du jour | liste fixée à l'avance (cycles de 30 jours, pas de retour avant 15 jours), date locale du joueur |
| Revoir une partie | adresse `index.html#partie12` |

## Arborescence

- `data/raw/` : fichiers bruts tels que téléchargés (ne jamais éditer à la main)
- `data/derived/` : tables prêtes pour le jeu et rapports de contrôle
- `docs/comparabilite.md` : fiches pays et limites de comparabilité
- `site/js/` : logique du jeu (distance, direction, treemap), testée
- `site/src/` → `site/dist/` : pages du site (jeu et règles), publiées par `.github/workflows/pages.yml`

Données © Union européenne, Eurostat (réutilisation avec mention de la source). Mécanique géographique : Tradle (MIT).
