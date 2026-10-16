# Budgetle

Jeu de devinette inspiré de Tradle : retrouver un pays à partir de ses dépenses publiques (70 pays, 5 continents).
Données préparées à l'avance, règles déterministes, page statique, aucune IA pendant les parties.

## Reproduire les données

```
python3 scripts/01_download.py        # données brutes Eurostat + centroïdes (data/raw, avec .meta.json : URL, date, SHA-256)
python3 scripts/02_build_profiles.py  # data/derived/profils_2024.{json,csv}, metadata.json, controles_2024.txt
npm install && node scripts/04_simulate.mjs   # vérifie geo.js contre geolib, simule les règles
python3 scripts/09_download_international.py  # FMI (COFOG, taux de change), OCDE (COFOG, PIB), BCE (contrôle des taux)
python3 scripts/10_build_world.py     # data/derived/profils_monde.{json,csv}, taux_de_change.csv, controles_monde.txt
python3 scripts/06_build_calendar.py  # data/derived/calendrier.json (pays du jour, 420 jours)
python3 scripts/11_fonts.py           # polices hébergées localement (site/fonts, licence OFL)
python3 scripts/05_build_site.py      # site/dist/index.html (jeu) et regles.html, pages autonomes, CSP
node scripts/05_check_site.mjs        # vérifie les données affichées et les affirmations des notes
node scripts/07_test_game.mjs         # tests de la logique de partie et du calendrier
python3 scripts/08_e2e.py             # partie complète jouée dans un navigateur (Playwright)
python3 scripts/12_check_security.py  # contrôles de sécurité (CSP, ressources externes, redirections, secrets)
```

## Choix arrêtés (séance 2, élargissement mondial inclus)

| Sujet | Choix |
|---|---|
| Périmètre | S13 (toutes APU), consolidé, dépense totale TE |
| Pays / année | 70 pays : 30 Eurostat (2024), 4 OCDE, 36 FMI ; année la plus récente par pays, 2022 au plus tôt ; comptes en caisse acceptés et signalés |
| Conversion en euros | taux moyen annuel FMI de l'année des données, contrôlé avec la BCE (17 devises, écart max 0,52 %) |
| Indice principal | montant total des dépenses en euros, puis (entre parenthèses) en % du PIB |
| Catégories | 10 divisions COFOG en % du PIB et en euros ; protection sociale détaillée en 7 sous-catégories |
| Treemap | surface et chiffre affiché = part dans la dépense totale ; % du PIB et montant au survol ou au toucher |
| Proximité | géographique avec boussole, formule et code de Tradle ; échelle mondiale (20 000 km) |
| Essais | 6 |
| Pays du jour | liste fixée à l'avance (cycles de 70 jours, pas de retour avant 35 jours), date locale du joueur |
| Revoir une partie | adresse `index.html#partie12` |
| Parties infinies | `index.html#infini` : pays tiré au hasard (hors 15 derniers), bouton « Pays suivant », score cumulé dans le navigateur |

## Arborescence

- `data/raw/` : fichiers bruts tels que téléchargés (ne jamais éditer à la main)
- `data/derived/` : tables prêtes pour le jeu et rapports de contrôle
- `docs/comparabilite.md` : fiches pays et limites de comparabilité
- `site/js/` : logique du jeu (distance, direction, treemap), testée
- `SECURITY.md` : mesures de sécurité et signalement
- `site/src/` → `site/dist/` : pages du site (jeu et règles), publiées par `.github/workflows/pages.yml`

Données : © Union européenne, Eurostat ; OCDE ; source : Fonds monétaire international ; BCE (contrôle). Mécanique géographique : Tradle (MIT).

Les fichiers bruts internationaux (data/raw/intl/*.csv, environ 30 Mo) ne sont pas versionnés : `09_download_international.py` les retélécharge et chaque `.meta.json` garde l'URL, la date et l'empreinte SHA-256 du téléchargement utilisé.
