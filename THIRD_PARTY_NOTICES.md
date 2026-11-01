# Sources et licences

Ce projet est spécifique au **Beekeeb Toucan v1**. Les éléments adaptés conservent les notices de leurs sources ; aucune réutilisation du cadre multiclaviers Ækeynox n’est nécessaire.

| Élément | Source et révision | Licence / notice |
|---|---|---|
| Matériel Toucan, configurations, écran et ressources | [beekeeb/zmk-keyboard-toucan](https://github.com/beekeeb/zmk-keyboard-toucan/tree/7154e0187128e493cd15785a18af1546419d5bb1) | [MIT](LICENSE), notices SPDX conservées ; provenance dans `provenance/upstream.json` |
| Tables Selenium HRM Vim, alias Ergo-L et comportements extraits/adaptés | [OneDeadKey/zmk-config-aekeynox](https://github.com/OneDeadKey/zmk-config-aekeynox/tree/3cadeede766f31bc1e34d7c9d8ee918073cf8478), `include/aekeynox/selenium.keymap`, `hold_taps.dtsi`, `mappings.dtsi`, `defaults.h`, `aliases.h` et `aliases/ergol.h` | [MIT — Copyright (c) 2024 The ZMK Contributors](licenses/selenium-MIT.txt) ; notices présentes dans les extraits |
| Police QuinqueFive utilisée par l’écran officiel | Ressources incluses dans le support Beekeeb | [SIL Open Font License 1.1](QuinqueFive_License.txt) |

Les dépendances ZMK, Zephyr, Cirque et RGB ne sont pas incorporées sous forme de code source dans ce dossier. Elles sont référencées par le manifeste et conservent leurs propres licences dans leurs dépôts respectifs. Leurs versions sont consignées dans [la provenance des dépendances](provenance/dependencies.json).

Les pages [Selenium](https://onedeadkey.github.io/selenium/) et [Ergo-L](https://ergol.org/) sont les références fonctionnelles. Les illustrations dérivées ne sont pas encore livrées ; leur provenance et leur droit de réutilisation devront être précisés lors de leur réalisation à l’étape 6.
