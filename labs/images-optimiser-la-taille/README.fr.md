# images-optimiser-la-taille : ce qu'une couche garde

## Ce que ce lab éprouve

Qu'une couche garde ce qu'une couche **suivante** supprime, et que le conteneur
ne montre rien de ce poids. Le cache n'y est pas visible, les artefacts utiles y
sont, le comportement est juste. Le défaut ne se voit qu'à la pesée.

## Mesuré avant d'être écrit

Sur `docker.lab`, le 2026-10-30, le même travail sous trois formes :

| Forme | Taille | Couches | Plus grosse couche |
| --- | --- | --- | --- |
| nettoyage une instruction trop tard | 52,3 Mo | 5 | **44 Mo** |
| nettoyage dans la même instruction | 14,6 Mo | 4 | 6,3 Mo |
| la seconde, aplatie | 14,6 Mo | **1** | 14,6 Mo |

Les trois produisent un conteneur identique. Et les deux fausses réponses ont
été **éprouvées** : le Dockerfile de départ rend **2/4**, refusé par les deux
pesées ; l'image aplatie rend **2/4** aussi, refusée par le partage de couches
et par la pesée par couche.

## Pourquoi quatre contrôles, et pourquoi deux pesées

Une couche peut rester sous son plafond pendant que plusieurs, ensemble, pèsent
le double du nécessaire : un cache écrit en deux fois, ou un second
téléchargement, se répartit sans jamais faire une grosse couche. La pesée
d'ensemble l'attrape, la pesée par couche attrape le nettoyage tardif. Les deux
sont nécessaires.

Le premier contrôle, lui, existe parce que **le moyen le plus rapide d'alléger
une image est de ne plus rien y mettre**. L'empreinte, tirée au hasard par
l'outil de fabrication au moment où il tourne, prouve que la fabrication a eu
lieu dans cette image.

## Pourquoi le quatrième contrôle refuse l'aplatissement

Il donne la bonne taille, et c'est bien le problème : les deux pesées seraient
vertes.

Les couches communes sont ce qui fait qu'un dépôt ne stocke le socle qu'une
fois, et qu'un poste qui l'a déjà ne télécharge que la différence. Une image
aplatie est stockée et transférée en entier, pour chaque variante : le gain
affiché est rendu au centuple. Le contrôle compare donc les couches du socle au
préfixe de celles de l'image.

## Un message qui accusait la mauvaise cause, et sa correction

Sur une image aplatie, la pesée par couche échoue aussi, puisque l'unique
couche porte tout. Le verdict était juste, et le message disait « cette couche
porte le cache », ce qui est **faux** : le cache n'y est pas.

Le contrôle regarde donc maintenant le partage de couches avant de conclure, et
dit alors que l'image a été aplatie, en renvoyant au contrôle qui en traite. Un
message qui nomme la mauvaise cause envoie chercher au mauvais endroit, et c'est
exactement ce que ce catalogue reproche au message du lab voisin sur le
contexte.

## Aucun seuil n'est écrit

Les contrôles pèsent le socle, puis les artefacts **dans l'image**, et
acceptent le socle plus deux fois les artefacts. Une valeur en dur serait fausse
dès que le socle change de version, et le lab refuserait alors un travail
correct.

La marge est large à dessein : la mesure donne 6,3 Mo pour la bonne écriture
contre 44 pour l'autre. Le seuil ne départage pas des cas limites, il sépare
deux mondes.

## Un défaut de sonde, attrapé par le cycle

Le premier jet lisait les couches avec un format Go écrit **nu** dans la
commande : `{{range .RootFS.Layers}}...` contient des espaces, le shell le
découpait, et docker recevait un format tronqué. La sonde rendait une sortie
vide, le contrôle **sautait** au lieu de refuser, et le cycle a rendu
« 3 passed, 1 skipped ».

La forme correcte passe le format par un paramètre, que testinfra quote. Et
l'erreur a valu un contrôle de plus : un détecteur a parcouru les **71**
fichiers de tests du catalogue à la recherche du même défaut, après avoir été
éprouvé sur un cas fautif et sur trois formes saines. Aucun autre lab n'était
touché.

Deux de ses jets antérieurs se trompaient, d'ailleurs : le premier se taisait
sur le cas exact qu'il cherchait, le second accusait deux labs attestés
parfaitement sains. **Un garde-fou s'éprouve dans les deux sens avant de
servir.**

## L'état de départ est cassé, et c'est la règle du dépôt

Le setup **ne construit pas** l'image : les quatre contrôles sont faux avant
tout travail. Une tâche vérifie que le socle existe, que l'image de l'apprenant
n'existe pas, et que le Dockerfile de départ porte bien son nettoyage tardif.

## Un piège du cleanup, payé d'avance

Le cache du constructeur part avec le reste. Ce lab **pèse des couches**, et un
cache survivant servirait une couche fabriquée au passage précédent, dont le
poids ne dirait plus rien du travail de l'apprenant.

## Ce que le lab n'exige pas

Un chemin. Le nettoyage s'écrit de plusieurs façons tant qu'il a lieu dans
l'instruction qui a créé ce qu'il retire. Le jeton est tiré par le setup, et
l'empreinte par l'outil de fabrication : rien n'est écrit en dur dans les
contrôles.
