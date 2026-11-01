# Compilation et provenance des firmwares

Le workflow `.github/workflows/build.yml` se lance lors des changements de la
branche `selenium-hrm`. `build.yaml` fournit les trois cibles Toucan v1.
L’ancienne branche `main` conserve son essai historique indépendant.

## Déroulement

Deux jobs propres, sans cache, effectuent chacun les mêmes opérations :

1. Vérifier les sources et l’environnement fixé.
2. Télécharger les dépendances et vérifier les six révisions directes.
3. Conserver le manifeste complet déclaré et le manifeste gelé des projets actifs.
4. Compiler gauche, droite et récupération ; conserver les diagnostics de chaque cible.
5. Contrôler la configuration, le devicetree et la structure des UF2 générés.

Un dernier job compare octet par octet les trois UF2 des deux constructions.
Le lot final est publié seulement si les deux builds, leurs contrôles et la
comparaison réussissent. Un échec sur une cible laisse les diagnostics des autres
cibles disponibles, mais ne valide pas la livraison.

## Artefacts d’une exécution

| Nom | Contenu |
|---|---|
| `toucan-v1-selenium-firmware` | Les UF2 gauche, droite et settings-reset, et `SHA256SUMS.txt` |
| `toucan-reproducibility-report` | Résultat de la comparaison binaire et commit source |
| `toucan-clean-pass-1` / `toucan-clean-pass-2` | Journaux, configurations, devicetrees, ELF, UF2 de diagnostic, versions d’outils, manifestes et rapports |

Les fichiers de diagnostic peuvent provenir d’une cible dont les contrôles ont
échoué. Le lot final `toucan-v1-selenium-firmware` constitue le résultat validé
par la chaîne de compilation. La procédure de flash est une étape distincte.

La conservation GitHub est de **14 jours**. Télécharger une copie durable des
firmwares et de leurs preuves lors d’une livraison ; le dépôt contient les sources
et la chaîne permettant de les reconstruire.

Le commit exact figure dans `provenance/build-summary.json` de chaque passe et
dans `reproducibility.json`. Pour refaire la même construction depuis GitHub,
ouvrir cette exécution et utiliser **Re-run all jobs** : cela reprend ce commit.
Une modification des paramètres dans `config/timing.h`, du keymap ou du matériel
demande une nouvelle compilation à partir du nouveau commit.

## Portée des contrôles

Les contrôles vérifient les cinq couches, les 42 positions physiques et les six
réserves, les temporisations, les rôles des moitiés, Studio désactivé, la pile
d’entrée, l’écran, le pavé et la structure UF2. Ils n’exécutent pas le firmware
sur un Toucan : voir le [plan d’essais matériels](test-plan.md).

L’identité binaire constatée concerne les deux builds du commit indiqué. Les
versions fixées et les limites de l’environnement sont décrites dans
[environment.md](environment.md).
