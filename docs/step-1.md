# Étape 1 — préparation terminée

**Bilan historique conservé.** Le projet courant a évolué depuis cette étape ; le portage est décrit dans [le bilan de l’étape 3](step-3.md). Les 172 contrôles ci-dessous concernent le témoin officiel archivé, pas la validation de Selenium.

Préparation achevée le **1er novembre 2026**, dans le périmètre du plan V1 validé.

## Résultat

Le projet local est prêt à recevoir le portage Selenium. Le support matériel officiel du Toucan v1 est conservé, les configurations sont utilisables sur Windows sans liens symboliques, et les six révisions principales sont fixées dans le manifeste. Les imports Zephyr ont été audités et leurs copies de lecture sont archivées.

Le socle contient encore le keymap officiel à 42 touches actives et Studio côté gauche, afin de servir de témoin. Les 36 touches actives, les cinq couches Selenium et leurs réglages seront développés à l’étape 3. L’installation du pilote Ergo-L par l’utilisateur constitue l’étape 2, possible en parallèle.

## Vérifications effectuées

- **172 contrôles statiques réussis sur 172**, aucun échec et aucun contrôle en attente dans ce périmètre.
- Provenance et empreintes des 47 fichiers officiels ; identité des descriptions matérielles et ressources conservées.
- Deux configurations ordinaires remplaçant les liens ; rôles gauche/droite, écran, tactile, 42 positions et pile à 2048 contrôlés dans les sources.
- Six révisions SHA et leurs URL/chemins ; imports et exclusions officiels conservés ; artefacts gauche/droite/reset distincts.
- Copies des manifestes audités vérifiées par leurs empreintes locales.
- Épreuves de détection réussies sur des copies de travail : pile abaissée à 512 et version ZMK remplacée par `main` rejetées ; provenance des versions absente signalée comme incomplète.

Trois avertissements sont attendus : deux incohérences ADJ héritées du keymap officiel, documentées sans correction silencieuse, et l’environnement de build encore à figer à l’étape 5.

## Limite de cette étape

**Aucune compilation ni production de firmware UF2, aucun flash, aucune installation système et aucune écriture GitHub n’ont été effectués.** L’environnement local a été inventorié ; la compilation est prévue dans GitHub Actions après l’accord distant de l’étape 4. Le résolveur west, les configurations générées et le fonctionnement physique seront contrôlés lors des builds et essais prévus au plan.

Les sources sont fixées ; l’image, le SDK, les outils et les actions du build restent à fixer avant la première compilation. Une identité binaire reproductible n’est donc pas encore revendiquée.

Rapports : [contrôles](../provenance/verification.json), [épreuves de détection](../provenance/verification-probes.json), [versions](../provenance/dependencies.json), [audit des imports](../provenance/manifest-audit.json).
