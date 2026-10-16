# Fiches de comparabilité — profils 2024

Statut de chaque affirmation :
**[Eurostat]** = note pays officielle (`data/raw/meta/gov_10a_exp_country_notes.txt`, métadonnées mises à jour le 16/09/2026) ;
**[Données]** = constat chiffré dans `data/raw/gov_10a_exp.csv` ;
**[Source externe]** = autre source citée ;
**[Hypothèse]** = explication plausible, non confirmée par une source officielle.

## Points généraux

- **Année 2024 retenue.** [Données] Au 16/10/2026, 2024 est la dernière année disponible pour les 30 pays ; seul le Luxembourg a publié 2025.
- **Données provisoires 2024** : Belgique, Allemagne, Espagne, France, Portugal, Slovaquie (toutes années), et répartition par fonction de l'Italie. [Eurostat]
- **Dénominateur des ratios** : PIB notifié dans le cadre de la procédure de déficit excessif (septembre-octobre 2025 ; avril 2026 pour le Luxembourg, le Portugal et la Suède). [Eurostat]
- **Montants en euros des pays hors zone euro** (BG, CZ, DK, HU, PL, RO, SE, CH, IS, NO) : ils dépendent du taux de change de l'année. Le % du PIB, affiché en premier dans le jeu, n'y est pas sensible. [Eurostat, métadonnées : unités MIO_EUR / MIO_NAC]
- **Correction de la séance 1** : la date de mise à jour annoncée alors (21/07/2026) provenait d'une lecture indirecte ; la date réelle du jeu téléchargé est le **16/09/2026**. Les valeurs, elles, sont identiques (0 écart sur 330 valeurs).

## Fiches pays

### Suisse — santé publique très faible (2,2 % du PIB)
- [Données] Produits médicaux 0,0 %, soins ambulatoires 0,2 %, hôpitaux 1,7 % du PIB, contre 1,5 / 3,1 / 3,7 % en France.
- [Hypothèse] L'assurance-maladie obligatoire (LAMal) est gérée par des caisses classées hors des administrations publiques : ce qu'elles remboursent n'apparaît donc pas dans S13. **Non confirmé par une source officielle à ce stade** (à vérifier auprès de l'Administration fédérale des finances).
- [Eurostat] Les intérêts (D.4) ne sont pas consolidés entre sous-secteurs. Impact faible en 2024 : la dette publique (01.7) représente 0,3 % du PIB.
- Usage dans le jeu : un indice « piège » très instructif sur la notion de périmètre public.

### Irlande — ratio au PIB anormalement bas (22,4 %)
- [Source externe] Le PIB irlandais est gonflé par les multinationales : amortissement de la propriété intellectuelle, flottes d'avions des sociétés de leasing. La banque centrale irlandaise utilise plutôt le RNB modifié (GNI*) de l'office statistique, le CSO.
- Conséquence : tous les % du PIB de l'Irlande sont « écrasés ». Les parts dans le total restent, elles, comparables.
- Usage dans le jeu : à signaler dans l'écran de fin (« pourquoi si bas ? »).

### Italie — logement à 4,4 % du PIB en 2023, 0,8 % en 2024
- [Données] Le pic se situe dans le groupe 06.1 (développement du logement) et passe presque entièrement par des transferts en capital (D.9) : 2,1 % en 2021, 2,9 % en 2022, 4,0 % en 2023, puis 0,3 % en 2024.
- [Source externe] Eurostat a validé l'enregistrement des crédits d'impôt Superbonus de 2023 comme « crédits payables », donc comme dépense publique l'année où ils sont acquis. Le traitement de 2024 restait à réexaminer.
- [Hypothèse] La chute de 2024 reflète la fin du dispositif et/ou un changement de traitement comptable.
- [Eurostat] La répartition par fonction 2024 est provisoire.
- Usage dans le jeu : justifie le choix d'une seule année. Le profil 2024 de l'Italie n'est pas affecté par le pic.

### Norvège
- [Eurostat] Les intérêts (D.4) ne sont pas consolidés ; la sécurité sociale (S.1314) est incluse dans l'État central. Ce second point est sans effet sur le total S13.
- [Hypothèse, à vérifier] Le PIB inclut l'activité pétrolière offshore, ce qui abaisse les ratios par rapport au « PIB continental » souvent utilisé en Norvège.

### Belgique
- [Eurostat] Des mesures énergétiques classées en 04.3 (combustibles et énergie) seront reclassées en 10.7 (exclusion sociale) à la prochaine transmission. La répartition Affaires économiques / Protection sociale de 2024 pourra donc bouger.

### Espagne
- [Eurostat] En 2024, des remboursements d'impôts consécutifs à des décisions de justice sont classés en 01.6 et 04.9 (catégories « non classées ailleurs »).

### Bulgarie
- [Eurostat] Le niveau II (sous-catégories) est provisoire.
- [Données] Le groupe 10.8 (R&D protection sociale) est manquant (drapeau `m`). Il est laissé vide, jamais mis à 0. Sa contribution est négligeable : 10.1 à 10.9 somment à GF10 à 0,000 % près.

### Finlande
- [Eurostat] Rupture de séries entre 2022 et 2023, liée à la création des « wellbeing services counties ». Elle touche surtout les services généraux, la santé et la protection sociale.
- Sans effet sur une comparaison entre pays en 2024, mais à garder en tête pour tout historique.

### Danemark, Finlande
- [Eurostat / Données] Quelques valeurs négatives sont en cours d'examen. En 2024, seul FI 04.9 = −2 M€, ce qui est négligeable.

### Luxembourg
- [Données] Dépense par habitant très élevée (59 500 €). Elle n'est pas affichée dans le jeu.
- [Hypothèse] L'effet vient du grand nombre de travailleurs frontaliers : ils contribuent au PIB et reçoivent des prestations, mais ne sont pas comptés dans la population.

## Sources
- Eurostat, métadonnées gov_10a_exp (section 19, notes pays) : https://ec.europa.eu/eurostat/cache/metadata/en/gov_10a_exp_esms.htm
- Eurostat, avis sur l'enregistrement du Superbonus 2023 : https://ec.europa.eu/eurostat/documents/1015035/16177999/IT+Advice+on+recording+of+2023+Superbonus.pdf
- Central Bank of Ireland, Economic Letter (janvier 2021) : https://www.centralbank.ie/news/article/press-release-economic-letter-is-ireland-really-the-most-prosperous-country-in-europe-04-january-2021

## Élargissement mondial (70 pays)

Règles de sélection et transformations : en-tête de `scripts/10_build_world.py` ; rapport chiffré : `data/derived/controles_monde.txt`.

- **Sources.** [Données] FMI GFS_COFOG pour 36 pays, OCDE pour l'Australie, la Corée, le Chili et la Colombie. Pour les pays européens, Eurostat reste la source. Le FMI reprend les mêmes chiffres qu'Eurostat pour l'Allemagne ; pour la Suisse, la dépense totale du FMI est inférieure de 3,6 % à celle d'Eurostat (millésimes ou périmètres différents).
- **Exclus.** Hong Kong et Macao (territoires) ; Somalie (pas de taux de change 2024) ; Ouzbékistan (les fonctions ne couvrent que 90 % du total publié). Pays publiés seulement pour l'État central (Argentine, Philippines, Éthiopie…) : non retenus.
- **Comptes en caisse (14 pays).** Arménie, Azerbaïdjan, Biélorussie, Géorgie, Indonésie, Kazakhstan, Kirghizistan, Kiribati, Kosovo, Moldavie, Mongolie, Singapour, Tadjikistan, Ukraine. Signalé en fin de partie.
- **Détail de la protection sociale non publié (8 pays).** Canada, Chili, Chine, Corée du Sud, Indonésie, Kiribati, Nouvelle-Zélande, États-Unis.
- **Fonctions publiées à zéro.** États-Unis : environnement (fonction non isolée). Signalé en fin de partie ; aucun « fait marquant » n'est tiré d'une fonction nulle.
- **Cas extrêmes, réels.** Kiribati : dépense publique de 96 % du PIB (petit État insulaire, recettes de licences de pêche et aides). Ukraine 2023 : défense 43 % de la dépense publique. [Hypothèse] pour l'explication de Kiribati.
- **Années.** 2022 (Namibie), 2023 (Albanie, Indonésie, Kazakhstan, Kenya, Kiribati, Corée, Ukraine), 2025 (Maurice, Nouvelle-Zélande, Turquie) ; 2024 pour les autres. L'année n'est révélée qu'en fin de partie.
- **Exercices budgétaires.** [À vérifier] Pour certains pays (Japon, Nouvelle-Zélande, Australie, Royaume-Uni…), les données annuelles du FMI peuvent correspondre à l'exercice budgétaire plutôt qu'à l'année civile ; le taux de change utilisé est la moyenne de l'année civile.
- **Taux de change.** [Données] Taux FMI (monnaie nationale pour 1 €, moyenne annuelle) ; pour les 17 pays dont la BCE publie la devise, écart maximal 0,52 % (livre turque, 2025). La méthode reproduit les euros d'Eurostat à 0,13 % près pour les pays européens hors zone euro.
