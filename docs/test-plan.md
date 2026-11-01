# Essais V1 à effectuer après compilation et flash

**Plan à exécuter ultérieurement : aucun résultat physique n'est revendiqué ici.**
L'assistant fournira les deux firmwares, leur référence de version, la procédure
de flash et l'aide-mémoire illustré à l'étape 6. L'utilisateur effectuera les
manipulations et les essais ; l'assistant analysera les écarts et corrigera le
firmware.

La [description des cinq couches](keymap.md) donne les positions. Commencer avec
les seuils de référence 300/150 ms ; ne pas changer plusieurs paramètres avant
d'avoir décrit une erreur reproductible.

## Préparer une séance

Noter la version du firmware, la version du pilote Ergo-L, la connexion USB ou
Bluetooth et l'application. Sélectionner Ergo-L sur Windows. Utiliser un document
de test, sans raccourcis susceptibles de fermer un travail non enregistré.

Pour chaque anomalie, indiquer les touches, **leur ordre d'appui et de relâchement**,
le résultat attendu, celui observé et la possibilité de reproduire le problème.
Un court exemple de texte est plus utile que « les HRM ne marchent pas ».

## 1. Vérifier le matériel et les positions

| Essai | Manipulation | Résultat à vérifier |
|---|---|---|
| Deux moitiés | Activer les deux côtés ; saisir alternativement à gauche et à droite | Aucune moitié muette, touche inversée, doublée ou perdue |
| Positions | Parcourir les 30 touches principales puis les 6 pouces avec l'aide-mémoire | Correspondance avec Base ; fonctions des pouces identifiables |
| Six réserves | Presser les positions 0, 11, 12, 23, 24, 35, en Base puis dans chacune des quatre autres couches | Aucune frappe, aucun modificateur ni changement de couche |
| USB et Bluetooth | Refaire une courte saisie et les essais du pavé dans chaque connexion | Texte et pointage fonctionnent ; sortie vers le bon ordinateur |
| Écran et pavé | Observer batterie/couche/connexion ; déplacer le pointeur et tester le tactile d'origine | Écran cohérent, pointage utilisable, pas de blocage après usage prolongé |

L'usage courant reste à 36 touches. Les six réserves ne doivent pas devenir
actives par transparence, par combo ou pendant un maintien.

## 2. Valider les lettres, les couches et les temporisations

| Essai | Séquence à essayer | Résultat à vérifier |
|---|---|---|
| Frappe ordinaire | Saisir lentement puis à vitesse habituelle un texte contenant les lettres de repos | Lettres correctes, pas de Ctrl/Alt/Win involontaire |
| HRM maintenu | Maintenir successivement les HRM au-delà de 300 ms puis effectuer une combinaison connue | Modificateur attendu ; après relâchement, la lettre redevient normale |
| Fenêtre 300 ms | Enchaîner rapidement une lettre HRM et une autre lettre, avec un léger chevauchement | Texte conservé ; relever toute transformation en raccourci |
| Fenêtre 150 ms | Frapper brièvement Retour arrière/Échap/Entrée ; puis les maintenir pour utiliser VimNav/FnMedia/NumRow | Frappe simple dans le premier cas ; couche dans le second, sans caractère parasite |
| Interruption d'un maintien | Maintenir brièvement Retour arrière/VimNav et presser une flèche avant 150 ms | Navigation, sans Retour arrière accidentel ; comportement distinct d'une lettre HRM |
| Répétition rapide | Frapper une lettre HRM puis la maintenir de nouveau dans les 200 ms ; refaire avec Espace | Répétition de la frappe, sans bascule intempestive en modificateur/couche |
| Sortie de couche | Activer puis relâcher chaque couche et saisir `azerty` ou une courte phrase repère | Retour à Base ; aucune couche persistante |

Les temps ci-dessus sont des repères ; un chronométrage manuel au milliseconde
près n'est pas demandé. L'ordre des événements compte autant que la durée.

## 3. Tester les enchaînements qui peuvent coincer un état

1. **Shift sticky et frappe chevauchante.** Toucher Shift, puis saisir deux lettres
   en maintenant légèrement la première pendant l'appui de la seconde. Une seule
   majuscule est attendue. Répéter avec plusieurs paires. Maintenir ensuite Shift
   pour plusieurs lettres : toutes doivent être en majuscules jusqu'au relâchement.
2. **Expiration.** Toucher Shift ou Symboles, attendre plus d'une seconde, puis
   saisir une lettre. La commande sticky expirée ne doit plus s'appliquer.
   Tester aussi deux appuis Shift : aucune activation de CapsWord/CapsLock.
3. **Symboles et chiffres.** Toucher Symboles puis saisir un signe ; revenir au
   texte. Enchaîner ensuite Symboles → pouce NumRow sticky (36) → chiffre de la
   rangée de repos, en restant sous le délai d'expiration. Si les deux commandes
   ont été touchées puis relâchées, la frappe suivante doit retrouver Base. Refaire
   en maintenant physiquement Symboles : après le chiffre, cette couche doit
   rester disponible. Essayer des chaînes telles que `(1)` ou `[2]`, sans maintien
   ni couche oublié.
4. **Retour Base par AltGr.** Maintenir VimNav, toucher son pouce 41, puis saisir
   un caractère AltGr du pilote Ergo-L. Refaire en maintenant ce pouce pour deux
   caractères. Le retour à Base et le relâchement d'AltGr doivent fonctionner.
   Relâcher ensuite tous les pouces et vérifier une phrase ordinaire.
5. **Ctrl+Shift+flèches.** Maintenir d'abord un HRM Ctrl de Base, puis Shift et
   VimNav ; utiliser les flèches pour sélectionner du texte. Relâcher les touches
   dans plusieurs ordres. La sélection doit correspondre à Ctrl+Shift+flèche,
   puis la frappe suivante doit redevenir normale.
6. **Alt+Tab et raccourcis.** Pour Alt+Tab, maintenir le HRM Alt droit, ouvrir
   VimNav au pouce gauche et utiliser Tab/Shift+Tab à gauche. Essayer aussi
   Ctrl+A/Z/X/C/V/S, les combinaisons de plusieurs modificateurs et Ctrl+F5 ou
   Alt+F4 depuis FnMedia sur une fenêtre de test. Aucun modificateur ne doit
   rester actif après le relâchement.

Si un état semble coincé, noter d'abord la séquence exacte, relâcher toutes les
touches et attendre l'expiration sticky. Ne pas utiliser `settings_reset` pour
masquer un défaut de frappe : il effacerait des réglages sans diagnostiquer le bug.

## 4. Valider Ergo-L natif et ses espaces

Saisir au minimum ce corpus dans un éditeur simple, un navigateur, un traitement
de texte et un terminal :

```text
é è à ù ç â ê î ô û ï œ æ
É È À Ù Ç Â Ê Î Ô Û Ï Œ Æ
' ’ " « » … ^ ~ - , . : / (1) [2] {3}
```

Vérifier les séquences Typo, les majuscules accentuées et leur annulation selon
le pilote. Les littéraux `^` et `~` ne doivent pas laisser un accent mort actif
pour la lettre suivante.

- **Shift+Espace :** espace insécable fine U+202F.
- **Shift+Symboles+Espace :** Shift+AltGr+Espace, espace insécable U+00A0. Tester
  les variantes sticky et maintenue de Shift/Symboles.
- **Typo puis Espace :** apostrophe typographique.

Les deux espaces se ressemblent visuellement : conserver le texte obtenu pour
que l'assistant vérifie leurs codes. La V1 ne doit pas dépendre de Verr Num pour
produire ces caractères.

## 5. Vérifier le défilement et les changements de contexte

| État | Essai du pavé | Résultat attendu |
|---|---|---|
| Base | Déplacer le doigt | Pointeur normal |
| Symboles seul, y compris sticky | Déplacer le doigt | Pointeur normal |
| NumRow seul | Déplacer le doigt | Pointeur normal |
| VimNav actif | Déplacer verticalement puis horizontalement | Défilement sur les deux axes |
| FnMedia ouvert depuis VimNav maintenu | Déplacer le doigt | Défilement, car VimNav est toujours actif en dessous |
| FnMedia ouvert directement depuis Base | Déplacer le doigt | Pointeur normal |
| Retour à Base | Relâcher les couches puis déplacer le doigt | Pointeur normal, sans défilement résiduel |

Tester également les quatre touches de défilement de VimNav et une utilisation
prolongée du pavé. Noter sens, vitesse, précision et tout blocage ; la V2 ajoutera
les actions souris complètes, pas cette première validation.

## 6. Connexions, maintenance, veille et reprise

- Vérifier la sélection des cinq profils Bluetooth 0 à 4. Les profils ne sont pas
  cinq ordinateurs déjà appairés : un emplacement vide doit d'abord être associé.
- Tester la bascule USB/Bluetooth depuis FnMedia41 et vérifier quel hôte reçoit
  réellement la frappe.
- **Effacement Bluetooth : uniquement sur un profil de validation.** Sélectionner
  ce profil, puis utiliser Shift gauche + la touche Profil 1 de FnMedia. C'est
  l'appariement du **profil actif** qui doit disparaître, même si ce n'est pas le
  profil 1. Les autres profils doivent rester utilisables ; réappairer celui testé.
- Avec la procédure fournie, vérifier séparément Bootloader (FnMedia37) et
  redémarrage (FnMedia40). Ces commandes interrompent la session en cours et ne
  font pas partie d'une frappe normale.
- Après une pause d'inactivité, une veille longue, puis un arrêt/rallumage des
  moitiés, vérifier la reconnexion, l'écran, le pavé et la première phrase. Les
  délais initiaux sont 30 secondes pour l'inactivité et 60 minutes pour le sommeil ;
  faire l'essai long au cours d'un usage réel plutôt que modifier les réglages.
- Refaire une séquence Shift/HRM, puis passer au pointage et revenir au texte.
  Aucun bouton, modificateur ou mode de défilement ne doit rester actif après
  reprise ou changement de connexion.

## Clore une version d'essai

Une version est candidate à la stabilité lorsque les fonctions utiles ont été
essayées, les anomalies reproductibles corrigées et les scénarios concernés
retestés. L'utilisateur confirme le confort réel ; l'assistant tient la liste des
bugs et fournit la version corrigée avec son aide-mémoire. Une compilation réussie
ne remplace aucun de ces essais.
