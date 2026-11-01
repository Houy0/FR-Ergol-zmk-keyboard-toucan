# Étape 3 — développement de Selenium HRM Vim

Développement local du **1er novembre 2026**, sur le socle Beekeeb fixé à l’étape 1. L’étape 2 a confirmé le pilote Ergo-L Windows existant, les majuscules accentuées, les ligatures et les deux espaces insécables ; le doublon KbdEdit a été retiré et le test refait avec succès.

## Résultat développé

| Élément | Réalisation |
|---|---|
| Couches | Base, Symbols, VimNav, NumRow, FnMedia, dans cet ordre de priorité |
| Touches réservées | `&none` aux indices 0, 11, 12, 23, 24 et 35 sur les cinq couches ; aucun combo |
| HRM | Alt, Ctrl et GUI symétriques sur la rangée de repos ; Print Screen simple dans FnMedia, sans Shift HRM |
| Pouces | Shift mémorisé/maintenu, Backspace/VimNav, Escape/FnMedia, Enter/NumRow, Space/VimNav et Symboles ; accès secondaires conformes à la variante Vim retenue |
| Temporisations | `config/timing.h` : tap-preferred 300 ms, hold-preferred 150 ms, quick-tap 200 ms ; expiration sticky distincte 1000 ms |
| Caractères | Alias natifs Ergo-L ; Typo ★ gérée par le pilote, sans couche d’émulation dans le firmware |
| Matériel | Matrice 42 positions, GPIO, rôles split, écran, Cirque, énergie et pile 2048 conservés |
| Pavé tactile V1 | Vitesse et inversion officielles ; passage au défilement lorsque VimNav est active |
| Configuration | Un seul keymap actif, y compris depuis le fallback du shield ; Studio désactivé explicitement dans les deux cibles de build |
| Maintenance | Cinq profils Bluetooth, effacement du profil sélectionné avec Shift, sélection USB/Bluetooth, bootloader et redémarrage accessibles depuis les 36 touches |

Le fichier personnalisé est nommé `selenium-behaviors.dtsi` pour éviter de masquer l’en-tête standard ZMK `behaviors.dtsi`. Aucun module dead-key ou mod-hold de la référence multiclaviers n’est requis.

## Adaptations déclarées

- Les colonnes extérieures sont volontairement sans action. Tab et Shift+Tab restent dans VimNav.
- Shift au pouce est un sticky/maintien simple, également dans VimNav ; les commandes CapsWord et CapsLock au pouce de la référence ne sont pas reprises. Aucun double Shift spécial n’est ajouté.
- Le Shift HRM de Print Screen est remplacé par Print Screen simple.
- FnMedia reçoit les profils Bluetooth 3 et 4 dans des cases libres et le choix USB/Bluetooth à la place du déverrouillage Studio. L’effacement reste associé à Shift + la touche de profil 1 ; il efface le **profil sélectionné**.
- Le défilement ne dépend plus des anciens numéros de couches NAV/SYM : il cible la constante VimNav. Une couche supérieure active ne l’annule pas tant que VimNav reste active.
- Les seuils sont centralisés, et le layer-tap tap-preferred est défini explicitement au lieu de modifier le comportement ZMK générique. Les autres primitives et l’ordre des commandes sticky/AltGr restent ceux de la référence.

Les originaux remplacés sont archivés dans `reference/baseline/`. La provenance initiale `provenance/upstream.json` et les rapports de l’étape 1 restent des relevés historiques. Le nouveau fichier `provenance/port.json` décrit les écarts et les sources de Selenium. Les notices MIT et SIL OFL sont conservées.

## Vérifications et limites

Une revue indépendante a comparé les cinq couches, les alias natifs et les comportements à la source Selenium figée. Les seuils et l’ordre des opérations de relâchement ont été relus. **350 contrôles statiques sur 350 sont réussis**, sans échec ni contrôle en attente dans ce périmètre. L’unique avertissement concerne l’environnement de compilation à figer à l’étape 5. Le vérificateur local dédié produit son bilan dans [port-verification.json](../provenance/port-verification.json).

**Cinq épreuves de détection ont réussi sur des copies isolées** : touche extérieure réactivée, seuil de maintien lié par erreur au seuil tap, défilement activé par Symboles, alias inconnu et transfert du paramètre de relâchement manquant dans la macro AltGr. Elles confirment que le vérificateur rejette ces erreurs ; elles ne simulent pas le firmware. Résultats dans [port-verification-probes.json](../provenance/port-verification-probes.json).

Ces contrôles portent sur les sources. **Aucune compilation, aucun fichier UF2, aucun flash ni essai physique du nouveau firmware n’ont encore été réalisés.** Ils ne démontrent pas les délais réellement perçus, l’absence de modificateur coincé en frappe rapide ou le comportement final du pavé. La compilation et l’inspection des configurations générées restent à l’étape 5, puis les essais physiques aux étapes 7 et 8.

L’[aide des couches](keymap.md) décrit la configuration écrite. Le [plan d’essais](test-plan.md) prépare les vérifications à effectuer après le flash. L’aide-mémoire illustrée et les instructions de flash restent prévues à l’étape 6.

## Suite

L’utilisateur a ensuite autorisé l’étape 4 : publier le portage sur une nouvelle branche `selenium-hrm` du fork public existant `Houy0/FR-Ergol-zmk-keyboard-toucan`. Cette branche repart du commit officiel audité et conserve l’ancienne branche `main`. Aucun dépôt distant ni workflow actif n’avait été créé pendant l’étape 3. L’organisation retenue est détaillée dans [github.md](github.md).
