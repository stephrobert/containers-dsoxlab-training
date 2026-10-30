# images-build-multi-etapes : ce qui vient du socle ne se retire pas

## Ce que ce lab éprouve

Qu'un outillage venu du **socle** ne se désinstalle pas. Il n'a pas été installé
par une instruction, donc aucune instruction ne peut le retirer, et le cacher au
conteneur ne retire pas un octet à l'image.

C'est ce qui le distingue de `images-optimiser-la-taille` : là, le nettoyage
existait et était au mauvais endroit. Ici, il n'y a **rien** à nettoyer.

## Mesuré avant d'être écrit

Sur `docker.lab`, le 2026-10-30 :

| Image | Taille | Outillage présent |
| --- | --- | --- |
| socle d'exécution | 8,3 Mo | sans objet |
| socle d'atelier | 39,8 Mo | oui |
| une seule étape | 39,8 Mo | **oui** |
| deux étapes | 8,3 Mo | **non** |

L'image à deux étapes pèse exactement **85 octets** de plus que son socle. Et
l'empreinte de fabrication change quand la source change, reste stable sinon :
c'est ce qui rend le quatrième contrôle fiable sans dépendre du cache.

La fausse réponse a été **éprouvée** : un `rm -rf` de l'outillage dans une
instruction suivante rend l'outillage invisible dans le conteneur, l'image pèse
**39,8 Mo**, et le score est **2/4**.

## Pourquoi l'outil refuse de tourner sans son outillage

Sans ce refus, la réponse la plus courte serait de fabriquer directement sur le
socle d'exécution, et le lab ne porterait sur rien : il n'y aurait plus de
raison d'avoir deux étapes.

Ce n'est pas un artifice : c'est la situation réelle. Un compilateur, un
gestionnaire de dépendances, une chaîne de construction sont absents d'une image
d'exécution par conception, et c'est précisément pourquoi la construction en
plusieurs étapes existe.

## Pourquoi le deuxième contrôle pèse en plus de chercher

L'absence des fichiers dit que le conteneur ne les voit plus. Le poids dit
qu'ils ne sont plus dans l'image.

Un `rm -rf` dans une instruction suivante donne la première sans la seconde, et
un contrôle qui ne chercherait que les fichiers récompenserait exactement la
faute que `images-optimiser-la-taille` a enseigné à reconnaître.

## Pourquoi le troisième contrôle regarde dans les deux sens

Il exige que les couches du socle d'exécution soient le préfixe de celles de
l'image, **et** que celles de l'atelier ne le soient pas.

La seconde moitié n'est pas une redite : une image pourrait être légère et
dériver encore de l'atelier, si son outillage avait été retiré autrement. Elle
porterait alors les couches de l'atelier, qu'un dépôt stocke et transfère avec
elle.

## Pourquoi le quatrième contrôle existe

Les trois premiers passeraient sur un produit **recopié** depuis l'hôte, à
condition d'y écrire une empreinte à la main. Celui-ci ferme la porte autrement :
il change la source dans une copie du contexte et exige que le produit suive.

C'est la même méthode que le contrôle de la source unique dans
`images-contexte-de-build`, et pour la même raison : une dépendance se prouve en
changeant ce dont on dépend.

## Aucun seuil n'est écrit

Le plafond de poids est dérivé du socle d'exécution, pesé à la notation. La
marge accordée est le double du socle, alors que la bonne réponse donne 85
octets de plus : le seuil ne départage pas des cas limites, il sépare 8 Mo de
39.

## L'état de départ est cassé, et c'est la règle du dépôt

Le setup ne construit pas l'image de l'apprenant : les quatre contrôles sont
faux avant tout travail. Une tâche vérifie que les deux socles existent, que
l'image de l'apprenant n'existe pas, et que le Dockerfile de départ part bien de
l'atelier.

## Un piège du cleanup, payé d'avance

Le cache du constructeur part avec le reste. Les contrôles reconstruisent pour
vérifier qu'une fabrication a lieu, et une étape servie par un cache du passage
précédent rendrait une empreinte qui ne dit plus rien du travail de l'apprenant.

## Ce que le lab n'exige pas

Un chemin. L'étape de fabrication peut être nommée ou désignée autrement, le
Dockerfile peut être réécrit ou doublé. Le jeton et la source sont tirés par le
setup, l'empreinte par la fabrication : rien n'est écrit en dur dans les
contrôles.
