# Environnement de compilation

État vérifié sur le poste Windows le **1er novembre 2026**.

| Élément | Résultat |
|---|---|
| Git | Disponible dans le runtime Codex. |
| Python | Interpréteur réel **3.12.14** disponible dans le runtime Codex ; pip **26.2.2**. Les commandes usuelles `python` et `python3` pointent vers les alias WindowsApps. |
| WSL | L’exécutable Windows existe, mais sa commande d’inventaire indique explicitement que WSL n’est pas installé. Aucune distribution utilisable identifiée. |
| CMake, Ninja, West | Absents du PATH et des emplacements usuels contrôlés. Les modules Python correspondants et `elftools` sont également absents de l’interpréteur vérifié. |
| Compilateur ARM / SDK Zephyr | Aucun outil ou SDK trouvé dans les emplacements usuels contrôlés ; variables d’environnement Zephyr non définies. |
| Docker | Commande et installation usuelle non trouvées. |

Cette recherche était ciblée : commandes disponibles, répertoires d’installation usuels et runtime Codex courant. Elle ne constitue pas un inventaire exhaustif du disque. Aucun refus d’accès n’a empêché ces contrôles ; l’absence de WSL est déclarée par Windows.

## Voie de compilation retenue pour la suite

La première compilation est prévue dans **GitHub Actions**, après accord explicite sur la création ou la modification du dépôt distant. L’absence de chaîne locale ne bloque donc pas la préparation et la revue du socle. Aucune installation Windows, WSL ou SDK n’est nécessaire à cette étape.

Les contrôles locaux de fichiers, de provenance et de configuration restent distincts d’une compilation. Aucun build n’a été exécuté et aucun firmware issu de ce socle n’est actuellement disponible pour le flash.

Les révisions directes retenues doivent rester identifiables dans le manifeste et le workflow. Cela ne démontre pas à lui seul le verrouillage des dépendances transitives, de l’image de compilation ou du SDK. La première exécution devra conserver ses journaux et les versions effectivement utilisées avant de conclure à la reproductibilité.

## Actions réalisées sur le poste

Lecture de l’état des outils et vérification du Python fourni avec Codex uniquement : aucune installation, modification de configuration système, création de distribution WSL ou compilation locale.
