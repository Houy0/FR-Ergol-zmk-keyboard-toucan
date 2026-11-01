# Toucan v1 — Selenium HRM Vim et Ergo-L

Ce projet porte **Selenium HRM, variante Vim**, sur le **Beekeeb Toucan v1 d’origine**. Il est destiné à la branche [`selenium-hrm`](https://github.com/Houy0/FR-Ergol-zmk-keyboard-toucan/tree/selenium-hrm) du fork existant [`Houy0/FR-Ergol-zmk-keyboard-toucan`](https://github.com/Houy0/FR-Ergol-zmk-keyboard-toucan). Il nécessite la disposition **Ergo-L standard installée et sélectionnée sur l’ordinateur**. L’installation Windows de référence a été validée à l’étape 2, puis son doublon KbdEdit retiré et le test refait avec succès.

## Configuration développée

- **Cinq couches** : Base, Symbols, VimNav, NumRow et FnMedia.
- **36 touches utilisables** : 30 principales et 6 pouces. Les six touches des colonnes extérieures restent sans action sur chaque couche ; la matrice matérielle conserve ses 42 positions.
- **Shift au pouce uniquement** ; HRM Alt/Ctrl/GUI sur la rangée de repos, sans Shift HRM. Aucun CapsWord ni action spéciale au double Shift.
- **Seuils distincts dans [config/timing.h](config/timing.h)** : tap-preferred 300 ms, hold-preferred 150 ms, répétition quick-tap 200 ms. Expiration sticky séparée : 1000 ms. Toute modification demande une nouvelle compilation et un flash.
- Support Beekeeb conservé : centrale gauche et écran, Cirque à droite, GPIO, géométrie, énergie et pile d’entrée à 2048. Le défilement garde ses réglages officiels et s’active lorsque **VimNav** est active, y compris sous une couche supérieure.
- Bluetooth : accès aux cinq profils, effacement du profil sélectionné avec Shift, choix USB/Bluetooth et accès maintenance depuis les 36 touches.

La V1 fonctionne initialement **sans ZMK Studio** : la matrice de build le désactive explicitement sur les deux moitiés. Les fichiers compilés constituent la source de configuration. Le keymap du shield inclut celui de `config/`, ce qui évite un retour accidentel à l’ancienne disposition à 42 touches actives.

Les caractères et les raccourcis utilisent les codes destinés au pilote Ergo-L natif. La touche Typo ★ reste à sa position HID O. Il n’y a ni couche Typo dans le firmware, ni table Unicode ou émulation AZERTY/QWERTY. V2 pavé tactile et V3 émulations restent hors du développement actuel.

Les fonctions et accès sont décrits dans [le guide des cinq couches](docs/keymap.md). La variante Vim prépare l’organisation future du pavé ; elle n’impose pas d’utiliser l’éditeur Vim.

## Vérification locale

Avec Python 3.10 ou ultérieur (contrôlé ici avec Python 3.12.14) :

```text
python scripts/verify_port.py --root . --report provenance/port-verification.json
```

Ce contrôle vérifie les invariants des sources et les contraintes du portage. Il ne compile pas le firmware, ne remplace pas le préprocesseur ou les schémas ZMK et ne télécharge aucune dépendance. Le plan d’[essais après flash](docs/test-plan.md) distingue les gestes à vérifier réellement des contrôles de fichiers.

## Limite actuelle et suite

L’étape 5 prépare les compilations GitHub Actions sur `selenium-hrm`. L’image ARM pour Zephyr 3.5, son SDK et les actions sont fixés par empreinte. Deux constructions indépendantes sans cache doivent produire les trois mêmes UF2 avant leur livraison. Les configurations et devicetrees générés seront contrôlés et archivés avec les journaux. Une compilation réussie ne valide pas les gestes sur le clavier : les essais physiques restent nécessaires.

Le socle officiel figé à l’étape 1 reste identifiable dans les archives et la provenance. Son ancien vérificateur `scripts/verify_baseline.py` reste destiné à cette version témoin ; il n’est pas le vérificateur de la configuration Selenium courante.

## Repères

- [Socle matériel et écarts déclarés](docs/baseline.md)
- [Environnement et voie de compilation](docs/environment.md)
- [Versions et imports](docs/dependencies.md)
- [Bilan de l’étape 1](docs/step-1.md)
- [Bilan du développement — étape 3](docs/step-3.md)
- [Dépôt, branches et suivi Beekeeb](docs/github.md)
- [Écarts et provenance du portage](provenance/port.json)
- [Provenance du support Beekeeb](provenance/upstream.json)
- [Versions fixées](provenance/dependencies.json)

Les fichiers d’origine remplacés sont conservés sous `reference/baseline/`. [Les notices tierces](THIRD_PARTY_NOTICES.md) accompagnent les adaptations. La nouvelle branche repart du commit officiel audité ; elle ne reprend pas les modifications de l’ancien essai conservé dans `main`. Le workflow Selenium cible uniquement `selenium-hrm`. Les manipulations techniques et corrections sont assurées par l’assistant ; l’utilisateur conserve les arbitrages et les essais physiques.
