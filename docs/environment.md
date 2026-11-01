# Environnement de compilation

Le build est exécuté dans **GitHub Actions**, sur la branche `selenium-hrm`.
Aucune installation de WSL, Docker ou de SDK sur le poste Windows n’est nécessaire.

## Environnement fixé à l’étape 5

- Image de compilation ZMK pour **Zephyr 3.5**, architecture hôte amd64,
  fixée par digest `sha256:cd960ebaf95cbf73219f3ad975020b83df234ed699b394bd59af16d59580daa9`.
- **SDK Zephyr 0.16.3**, présent dans l’image. Les versions réelles de CMake,
  Ninja, west, Python et du compilateur sont conservées à chaque construction.
- Actions checkout, upload-artifact et download-artifact fixées par SHA Git complet.
- Les dépendances applicatives restent celles de `config/west.yml`, fixées par SHA.
  Le manifeste complet résolu est archivé avec les résultats.
- Aucun téléchargement de paquet Python ou système durant le build et aucun cache
  de dépendances ou de compilation restauré.

Les empreintes et leurs sources de vérification sont conservées dans
[`provenance/build-environment.json`](../provenance/build-environment.json).
Le tag `stable` observé pointait vers l’environnement Zephyr 4.1 : il n’a pas été
retenu pour ce projet basé sur Zephyr 3.5.

## Vérifications de compilation

Deux jobs indépendants construisent chacun les firmwares **gauche**, **droite** et
**settings-reset** à partir des mêmes sources. Les chemins de compilation sont
constants et `SOURCE_DATE_EPOCH` est fixé à la date du commit source.

Les configurations Kconfig et devicetrees générés, les outils utilisés, le manifeste
west résolu, les journaux et les contrôles des UF2 sont conservés en artefacts.
Un dernier job compare les trois fichiers UF2 des deux constructions avant de
publier le lot de firmwares utilisable pour l’étape de préparation au flash.

La comparaison démontre une identité binaire pour **ce commit et ces deux builds**.
Elle ne garantit pas à elle seule tous les environnements futurs : le noyau et
l’image du runner hôte restent gérés par GitHub. Le fonctionnement des touches,
des gestes sticky/HRM, du Bluetooth, de l’écran et du pavé exige les essais matériels.

## Poste Windows

Le contrôle initial du 1er novembre 2026 a identifié Git et Python 3.12.14 dans
le runtime Codex, sans chaîne locale west/CMake/Ninja/SDK, Docker ou distribution
WSL utilisable. La préparation du projet et les contrôles statiques s’exécutent
localement ; la compilation ARM s’exécute dans GitHub Actions.
