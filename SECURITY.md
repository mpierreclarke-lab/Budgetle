# Sécurité

Budgetle est un site statique : pas de serveur applicatif, pas de compte, pas de cookie, aucune donnée
personnelle collectée. Les parties sont enregistrées uniquement dans le navigateur du joueur (stockage local).

## Signaler un problème

Utilisez la fonction « Report a vulnerability » de l'onglet *Security* du dépôt (signalement privé),
plutôt qu'une issue publique.

## Mesures en place

- Pages publiques : politique de sécurité de contenu (CSP) n'autorisant que le site lui-même et le script
  de la page (empreinte SHA-256), aucune ressource externe, polices hébergées localement, `Referrer-Policy: no-referrer`.
- Aucune redirection, ouverture de fenêtre ou évaluation de code dans les pages (vérifié à chaque publication).
- Données du stockage local relues avec validation (codes de pays connus uniquement).
- Données insérées dans les pages contrôlées à la construction (pas de caractères HTML).
- Intégration continue : actions épinglées par empreinte de commit, mises à jour par Dependabot, jeton à droits minimaux.
- Contrôles automatiques : `scripts/12_check_security.py`.

## Limites connues

- GitHub Pages ne permet pas d'envoyer des en-têtes HTTP personnalisés : la protection contre l'intégration
  du site dans un cadre (`frame-ancestors`, `X-Frame-Options`) n'est pas disponible. Le site ne contient
  ni formulaire sensible ni action irréversible, ce qui limite ce risque.
