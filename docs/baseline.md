# Socle officiel Toucan v1

**Document historique de l’étape 1.** L’état témoin décrit ci-dessous précède le portage. Le dossier courant contient désormais Selenium : voir [l’étape 3](step-3.md), [le guide des couches](keymap.md) et [les écarts déclarés](../provenance/port.json). L’archive séparée de l’étape 1 n’a pas été modifiée.

Ce dossier prépare un **témoin du firmware officiel**, spécifique au Toucan v1. Il ne contient pas encore le portage Selenium HRM. Aucun build ni firmware à flasher n’a été produit.

Source : [Beekeeb `zmk-keyboard-toucan`, commit `7154e0187128e493cd15785a18af1546419d5bb1`](https://github.com/beekeeb/zmk-keyboard-toucan/tree/7154e0187128e493cd15785a18af1546419d5bb1). La liste des fichiers copiés, leurs empreintes et les écarts déclarés figurent dans [la provenance](../provenance/upstream.json). Les fichiers de configuration de build d’origine sont conservés sous `reference/`.

## Éléments conservés

| Élément | Socle retenu |
|---|---|
| Contrôleur | `seeeduino_xiao_ble` pour les deux moitiés. |
| Gauche | `toucan_left rgbled_adapter nice_view_gem`, rôle central et écran officiels. |
| Droite | `toucan_right rgbled_adapter`, rôle périphérique et pilote Cirque officiels. |
| Récupération | Cible distincte `settings_reset` sur le même contrôleur. |
| Studio | Activation officielle conservée à gauche : snippet `studio-rpc-usb-uart`, option `CONFIG_ZMK_STUDIO=y` et touche de déverrouillage du keymap d’origine. |
| Géométrie | 42 positions, pouces aux indices 36 à 41 ; matrice, GPIO et décalage de colonnes inchangés. |
| Pointage et écran | Descriptions matérielles, transformations, routage split et ressources d’écran d’origine conservés. |
| Énergie et batterie | Réglages officiels conservés, dont pile du thread d’entrée de 2048 octets sur chaque moitié, délai d’inactivité de 30 secondes et sommeil après une heure. |
| Keymap | Keymap officiel avec couches BASE, NAV, SYM et ADJ ; aucune conversion Selenium ni neutralisation des colonnes externes à ce stade. |

Le pointage matériel déjà présent est conservé dans le témoin. Les évolutions fonctionnelles du pavé tactile restent hors de cette préparation.

## Normalisation des configurations `.conf`

Quatre liens symboliques Git d’origine ne sont pas recopiés :

- `config/toucan_left.conf` et `config/toucan_right.conf` visaient tous deux `../boards/shields/toucan/toucan.conf`, absent de cette révision ;
- `toucan_left.conf` et `toucan_right.conf`, à la racine, étaient des alias vers les configurations réelles du shield.

Dans la copie préparée, les deux fichiers sous `config/` sont de **vrais fichiers Kconfig**, identiques aux configurations respectives présentes sous `boards/shields/toucan/`. Les deux alias de racine sont omis. Cette normalisation évite de dépendre de la matérialisation des liens sur Windows ou Linux ; elle ne change pas les valeurs des options d’origine.

Ces copies sont intentionnelles pour le témoin. Toute évolution ultérieure devra contrôler leur cohérence et les chemins de configuration effectivement chargés. Le build devra confirmer les valeurs finales dans les deux fichiers `.config`, notamment `CONFIG_INPUT_THREAD_STACK_SIZE=2048`, le pointage, les rôles split et l’activation de Studio à gauche.

## Deux anomalies héritées, conservées explicitement

Le keymap officiel contient dans ADJ :

- `&mo TAB` : un code de touche est utilisé comme indice de couche ;
- `&bt LSHFT` : un code de touche est utilisé comme commande Bluetooth.

Ces incohérences sémantiques sont conservées afin de ne pas corriger silencieusement le témoin. Elles ne suffisent pas à établir un échec de compilation. Le remplacement du keymap par Selenium les éliminera ; elles ne constituent pas des comportements à reproduire dans le portage.

## Limites de validation

La préparation conserve les descriptions matérielles et le keymap du commit source, en déclarant la normalisation ci-dessus. Elle ne prouve pas encore que les cibles compilent avec les références retenues ni que les fichiers de configuration sont chargés comme attendu.

La compilation GitHub Actions, après accord distant, devra vérifier les deux moitiés et le firmware de récupération, puis conserver les journaux et configurations finales. Aucune reproductibilité complète des dépendances transitives ou de l’image de compilation n’est annoncée avant ces vérifications. L’état du poste local est décrit dans [environment.md](environment.md).

Les licences MIT, les notices SPDX et la licence de la police QuinqueFive sont conservées avec les fichiers d’origine. Aucun code Selenium n’a encore été introduit dans ce socle.
