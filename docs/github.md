# Dépôt GitHub et suivi des mises à jour

Organisation autorisée par l’utilisateur le **1er novembre 2026**, pour l’étape 4.

| Élément | Choix |
|---|---|
| Dépôt | Fork public existant [Houy0/FR-Ergol-zmk-keyboard-toucan](https://github.com/Houy0/FR-Ergol-zmk-keyboard-toucan) |
| Projet Selenium | Nouvelle branche [`selenium-hrm`](https://github.com/Houy0/FR-Ergol-zmk-keyboard-toucan/tree/selenium-hrm) |
| Base de départ | Commit officiel Beekeeb `7154e0187128e493cd15785a18af1546419d5bb1` |
| Ancien essai | Branche `main` conservée avec son contenu et son historique |
| Branche par défaut du dépôt | Inchangée à cette étape |
| Compilation | Aucun workflow actif dans la nouvelle branche à l’étape 4 ; GitHub Actions prévu à l’étape 5 |

La nouvelle branche utilise le support officiel puis le portage validé à l’étape 3. Les modifications non fonctionnelles de l’ancien essai ne sont pas intégrées. Les deux versions coexistent dans le même fork.

## Consulter le bon projet

Ouvrir le lien de la branche `selenium-hrm` ci-dessus. La page principale du dépôt peut encore afficher `main` : elle correspond alors à l’ancien essai. Les futurs firmwares Selenium seront identifiés par leur branche et leur commit. Aucun firmware n’est encore fourni à cette étape.

## Intégrer une correction Beekeeb

Le lien avec [le dépôt officiel](https://github.com/beekeeb/zmk-keyboard-toucan) facilite la comparaison des changements. Leur intégration reste volontaire : l’assistant examine les corrections utiles, prépare la fusion et traite les conflits éventuels, puis vérifie la compilation et les essais concernés avant livraison.

Les versions de ZMK, Zephyr et des modules restent fixées par `config/west.yml`. Une correction dans le dépôt Beekeeb et un changement de version de ces dépendances sont deux opérations distinctes à vérifier.

Les empreintes de provenance de l’étape 1 restent des relevés historiques. Lorsqu’un fichier matériel ou une dépendance évoluera, les écarts et les contrôles associés devront être actualisés explicitement. La synchronisation d’un fork n’est pas une validation fonctionnelle.

## Préserver la configuration sur Windows

`.gitattributes` impose LF pour les fichiers texte et conserve quatre exceptions officielles en CRLF. Les fichiers `config/toucan_left.conf` et `config/toucan_right.conf` sont des fichiers ordinaires, pas les liens symboliques ambigus du dépôt initial. Ces choix doivent rester identiques après un clone ou un téléchargement du projet.

Références : [fonctionnement des forks GitHub](https://docs.github.com/en/pull-requests/reference/forks), [synchronisation d’un fork](https://docs.github.com/en/pull-requests/how-tos/work-with-forks/syncing-a-fork).
