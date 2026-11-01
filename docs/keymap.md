# Disposition V1 — Selenium HRM, variante Vim

Cette page décrit le firmware en cours de préparation. Elle ne constitue pas un
compte rendu de flash ou d'essais physiques. Les illustrations adaptées au Toucan
seront fournies à l'étape 6, avant les essais.

La V1 utilise **Ergo-L installé et sélectionné sur Windows**. Le Toucan transmet
les touches ; le pilote produit les lettres, accents et signes typographiques.
Il n'y a pas d'émulation AZERTY/QWERTY ni de couche Typo dans le firmware.

## Lire les positions

Les tableaux montrent les cinq touches principales de chaque main, de gauche à
droite. Chaque moitié possède aussi une colonne extérieure de trois touches,
volontairement sans action : six positions sont réservées dans toutes les couches.
Les trois pouces de chaque main restent actifs, soit **30 touches principales et
6 pouces**.

| Rangée | Réserve gauche | Main gauche | Main droite | Réserve droite |
|---|---|---|---|---|
| Haute | 0 | 1, 2, 3, 4, 5 | 6, 7, 8, 9, 10 | 11 |
| Repos | 12 | 13, 14, 15, 16, 17 | 18, 19, 20, 21, 22 | 23 |
| Basse | 24 | 25, 26, 27, 28, 29 | 30, 31, 32, 33, 34 | 35 |

Les pouces, de gauche à droite, portent les numéros **36, 37, 38 | 39, 40, 41**.
Dans les tableaux, `—` signifie aucune action et « hérité » signifie que la touche
garde la fonction de la couche active située en dessous.

## Base : texte et accès aux couches

Les légendes suivantes sont les sorties attendues avec Ergo-L natif. Dans la
rangée de repos, `lettre / modificateur` signifie **frappe brève / maintien**.
Win désigne la touche Windows. Le nom « variante Vim » décrit l'organisation de
la navigation ; utiliser le logiciel Vim n'est pas nécessaire.

| Rangée | Main gauche | Main droite |
|---|---|---|
| Haute | `q` · `c` · `o` · `p` · `w` | `j` · `m` · `d` · `★` · `y` |
| Repos | `a` · `s / Win` · `e / Ctrl` · `n / Alt` · `f` | `l` · `r / Alt` · `t / Ctrl` · `i / Win` · `u` |
| Basse | `z` · `x` · `-` · `v` · `b` | `.` · `h` · `g` · `,` · `k` |

Cette correspondance suit la [table officielle Ergo-L](https://github.com/Nuclear-Squid/ergol/blob/main/keymaps/fr/ergol.toml).
Les noms HID dans le fichier de développement restent QWERTY : par exemple,
`W` produit `c`, `O` produit Typo `★`, et `COMMA` produit `g`.

| Pouce | Frappe brève | Maintien |
|---|---|---|
| 36 — gauche extérieur | Shift pour la prochaine frappe | Shift immédiat et continu |
| 37 — gauche central | Retour arrière | VimNav |
| 38 — gauche intérieur | Échap | FnMedia |
| 39 — droit intérieur | Entrée | NumRow |
| 40 — droit central | Espace | VimNav |
| 41 — droit extérieur | Symboles pour la prochaine frappe | Symboles |

Shift est uniquement au pouce. Il n'y a ni Shift HRM, ni CapsWord, ni commande
spéciale CapsLock sur le double appui Shift. Pour combiner un modificateur de Base
avec une autre couche, le maintenir **avant** d'ouvrir cette couche : la touche
peut y avoir une autre fonction.

## Symboles

Chaque signe est accessible directement depuis cette couche, sans ajouter Shift.

| Rangée | Main gauche | Main droite |
|---|---|---|
| Haute | `^` · `<` · `>` · `$` · `%` | `@` · `&` · `*` · `'` · `` ` `` |
| Repos | `{` · `(` · `)` · `}` · `=` | `\` · `+` · `-` · `/` · `"` |
| Basse | `~` · `[` · `]` · `_` · `#` | `\|` · `!` · `;` · `:` · `?` |

| Pouce | Fonction dans Symboles |
|---|---|
| 36 | NumRow pour la prochaine frappe si touché ; NumRow si maintenu |
| 37 | Espace |
| 38 | Entrée |
| 39, 40, 41 | Fonctions héritées |

Avec **Shift seul déjà actif**, le pouce Symboles fournit **Shift+AltGr** pour les
accès natifs d'Ergo-L. Avec Ctrl, Win ou Alt actifs, il conserve la couche Symboles
pour les raccourcis. Ce changement de fonction est volontaire.

## VimNav : navigation et édition

Les flèches sont sur les positions physiques QWERTY H/J/K/L à droite : cela ne
correspond pas aux lettres `h/j/k/l` produites par Ergo-L.

| Rangée | Main gauche | Main droite |
|---|---|---|
| Haute | — · Fermer l'onglet · Précédent · Suivant · — | Début · Page bas · Page haut · Fin · Suppr |
| Repos | Tout sélectionner · Enregistrer · Shift+Tab · Tab · — | Gauche · Bas · Haut · Droite · — |
| Basse | Annuler · Couper · Copier · Coller · Rétablir | Défilement gauche · bas · haut · droite · — |

Précédent/Suivant envoient normalement Alt+flèche gauche/droite. Si Alt ou Win est
déjà maintenu, ils utilisent les variantes de touches prévues par Selenium ; leur
résultat dépend alors du raccourci de l'application.

| Pouce | Fonction dans VimNav |
|---|---|
| 36 | Shift sticky ou maintenu, comme en Base |
| 37 | Suppr si frappé ; FnMedia si maintenu |
| 38, 39 | Fonctions héritées |
| 40 | FnMedia tant qu'il est maintenu |
| 41 | Revient à Base puis fournit AltGr, sticky ou maintenu |

Tab est à la position 16, Shift+Tab à la position 15. L'accès AltGr du pouce 41
permet de revenir aux caractères natifs même en partant de la navigation.

**Pavé tactile :** quand VimNav est actif, ses déplacements deviennent du
défilement vertical/horizontal. Le pointeur normal revient lorsque VimNav est
quitté. Cette règle regarde si VimNav est encore actif, même si FnMedia ou NumRow
est au-dessus : ouvrir FnMedia depuis VimNav conserve donc le défilement. Ouvrir
FnMedia directement depuis Base, ou utiliser Symboles/NumRow seuls, ne l'active pas.

## NumRow : chiffres et ponctuation

| Rangée | Main gauche | Main droite |
|---|---|---|
| Haute | Versions avec Shift de `1 2 3 4 5` | Versions avec Shift de `6 7 8 9 0` |
| Repos | `1` · `2` · `3` · `4` · `5` | `6` · `7` · `8` · `9` · `0` |
| Basse | — · — · — · — · — | `-` · `,` · `.` · `:` · `/` |

La rangée supérieure utilise Shift droit à gauche et Shift gauche à droite,
conformément à Selenium ; la sortie est celle du pilote Ergo-L installé.

| Pouce | Fonction dans NumRow |
|---|---|
| 36, 38, 39 | Fonctions héritées |
| 37 | Shift droit + Espace |
| 40 | Shift gauche + Espace |
| 41 | AltGr maintenu |

## FnMedia : fonctions, multimédia et connexions

`action / modificateur` garde le sens **frappe brève / maintien**.

| Rangée | Main gauche | Main droite |
|---|---|---|
| Haute | F1 · F2 · F3 · F4 · Profil 3 | Profil 2 · Média suivant · Volume + · Luminosité + · Verr défil |
| Repos | F5 · F6 · F7 · F8 · Profil 4 | Profil 1 / effacement · Lecture-pause / Alt · Muet / Ctrl · Verrouiller / Win · Impr écran |
| Basse | F9 · F10 · F11 · F12 · — | Profil 0 · Média précédent · Volume − · Luminosité − · Inser |

Les cinq profils Bluetooth sont numérotés **0 à 4** dans le firmware. Choisir un
profil vide permet un nouvel appairage. Choisir un profil déjà associé sélectionne
cette connexion.

**Shift gauche + la commande « Profil 1 » efface l'appariement du profil
actuellement sélectionné**, qui peut être un autre profil que le 1. Il faudra le
réappairer. Sans Shift, cette même touche sélectionne simplement le profil 1.

| Pouce | Fonction dans FnMedia |
|---|---|
| 36, 38, 39 | Fonctions héritées |
| 37 | Bootloader : passage en mode de flash |
| 40 | Redémarrage du firmware |
| 41 | Bascule de la sortie USB/Bluetooth |

Pour accéder directement à ces commandes depuis Base, maintenir le pouce 38
(Échap/FnMedia), puis utiliser la touche voulue. La procédure détaillée de flash
et de récupération sera fournie avec les firmwares.

## Temporisations et gestes sticky

Les réglages sont centralisés dans [config/timing.h](../config/timing.h) :

| Réglage | Valeur initiale | Effet |
|---|---|---|
| `TAP_PREFERRED_MS` | 300 ms | Lettres HRM et Espace/VimNav privilégient la frappe |
| `HOLD_PREFERRED_MS` | 150 ms | Retour arrière, Échap et Entrée aux pouces privilégient la couche |
| `QUICK_TAP_MS` | 200 ms | Frapper puis maintenir rapidement la même touche répète sa frappe |
| `STICKY_TIMEOUT_MS` | 1000 ms | Expiration d'une commande sticky encore en attente |

Les deux seuils 300/150 ms sont indépendants. Une touche préférant le maintien
peut activer sa couche dès qu'une autre touche est pressée, sans attendre 150 ms.
Une lettre HRM privilégie au contraire sa lettre pendant la fenêtre de décision.
Le seuil des enveloppes sticky reste celui de 300 ms ; **Shift agit immédiatement
pendant la décision**. Le quick-tap ne s'applique pas aux enveloppes Shift/Symboles.

Ces paramètres sont des réglages de compilation : les changer demande une nouvelle
construction et un flash. Leur validation pratique se fait avec le
[plan d'essais](test-plan.md), avant tout réglage fin.

## Typo et écarts assumés

Typo `★`, les majuscules accentuées et les espaces insécables relèvent du pilote :
Typo puis lettre donne la variante correspondante ; Typo puis majuscule donne sa
majuscule accentuée. Shift+Espace donne l'insécable fine U+202F et
Shift+AltGr+Espace l'insécable U+00A0. Typo puis Espace donne l'apostrophe
typographique. Ces accès doivent être vérifiés lors des essais.

Par rapport au [code Selenium de référence](https://github.com/OneDeadKey/zmk-config-aekeynox/tree/3cadeede766f31bc1e34d7c9d8ee918073cf8478) :

- Cinq couches utiles conservées ; NavNum, NumLock interne, Callum et adaptations
  multiclaviers retirés. La matrice matérielle reste à 42 positions.
- Six colonnes extérieures sans action partout ; Shift HRM retiré de FnMedia,
  Impr écran reste une touche simple.
- Shift sticky simple en Base et VimNav ; CapsWord, CapsLock par tap en VimNav et
  double Shift spécial retirés.
- Profils Bluetooth 3/4 ajoutés ; commande Studio remplacée par la sortie USB/BLE.
- Défilement tactile limité à VimNav ; vitesse et inversion officielles conservées.
- Aucun module communautaire dead-key/mod-hold et aucune émulation de caractères.

Studio est désactivé dans cette préparation afin que les fichiers du projet
restent la référence pendant la mise au point.
