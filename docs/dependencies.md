# Versions des sources et imports

Révisions résolues le **1er novembre 2026**, puis enregistrées dans `config/west.yml` et `provenance/dependencies.json`.

| Projet | Référence d’origine | Commit retenu |
|---|---|---|
| ZMK | tag `v0.3` | `edf5c0814fd3ea202e43aad2d68fd32e882a518c` |
| Zephyr pour ZMK | branche `v3.5.0+zmk-fixes` | `dacab4875df72109b96cc8977547a0dc04875bcd` |
| Cirque | branche `toucan` | `effec100f0cd3a38e7fba3adfea394586cc84cab` |
| RGB LED widget | tag `v0.3` | `8756cb7b8114069fa3c25c6f6c990f24988fceff` |
| nanopb, fork ZMK | manifeste ZMK fixé | `8c60555d6277a0360c876bd85d491fc4fb0cd74a` |
| Messages Studio | manifeste ZMK fixé | `6cb4c283e76209d59c45fbcb218800cd19e9339d` |

Les quatre premières révisions ont été lues depuis les liens de commit des pages GitHub des références sélectionnées. Les deux dernières sont déjà fixées dans le manifeste ZMK. Les liens de preuve se trouvent dans le fichier JSON de provenance.

## Conservation des imports officiels

Le manifeste conserve `zmk.import: app/west.yml`. Zephyr est déclaré explicitement au niveau supérieur afin que son ancienne référence de branche soit remplacée par un commit immuable. Le bloc d’import Zephyr reprend les **18 exclusions officielles**, sans tenter de réduire davantage les modules avant compilation.

`nanopb` et `zmk-studio-messages` sont également explicites au niveau supérieur. Cela conserve notamment le fork et le chemin nanopb choisis par ZMK, au lieu de laisser le sous-manifeste optionnel de Zephyr gagner la priorité sur ce nom.

Les révisions SHA n’ont pas de `clone-depth` : cette option west est prévue pour les références de branche ou de tag. Les groupes `optional` et `babblesim` restent désactivés comme dans le manifeste Zephyr. Les fonctions de groupe exigent un schéma west d’au moins 0.10 ; la version exacte de l’outil sera fixée avec l’environnement de build, puis vérifiée réellement.

L’audit du manifeste Zephyr fixé a relevé 62 projets, tous à SHA complet. Le répertoire importé `submanifests/` contient `optional.yaml` comme seul manifeste YAML actif ; ses 9 projets sont également à SHA complet. Les copies de lecture et leur traçabilité sont conservées dans `reference/manifests/` et `provenance/manifest-audit.json`. Ce comptage ne signifie pas que les 71 projets seront actifs après exclusions et filtres.

## Ce qui reste à vérifier à la compilation

La fixation des sources et la lecture des imports sont achevées pour la préparation. **La résolution effective par west n’a pas été exécutée.** Après récupération du workspace, le build devra produire et archiver `west manifest --freeze`, puis contrôler les options et le devicetree de chaque moitié.

Le workflow officiel réutilisable appelle encore une image `stable` et des actions par étiquette. Une simple référence SHA de ce workflow ne suffirait donc pas à figer son environnement. Avant les premières compilations, l’étape des builds fixera l’image par digest, les actions par SHA et enregistrera les versions SDK/outils. Aucun workflow automatique actif n’est fourni à cette étape.

Les contrôles statiques ne démontrent pas encore une compilation réussie, un firmware fonctionnel ou une identité binaire entre deux constructions. La revue complète des licences transitives sera également à compléter lors de la préparation de la livraison ; les notices du code matériel déjà copié sont conservées.

Sources : [manifeste ZMK fixé](https://github.com/zmkfirmware/zmk/blob/edf5c0814fd3ea202e43aad2d68fd32e882a518c/app/west.yml), [manifeste Zephyr fixé](https://github.com/zmkfirmware/zephyr/blob/dacab4875df72109b96cc8977547a0dc04875bcd/west.yml), [sous-manifestes Zephyr](https://github.com/zmkfirmware/zephyr/tree/dacab4875df72109b96cc8977547a0dc04875bcd/submanifests), [règles west](https://docs.zephyrproject.org/latest/develop/west/manifest.html).
