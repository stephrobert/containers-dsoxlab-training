# Trois accès refusés, et pas une seule cause

## La situation

Trois conteneurs d'une même chaîne ne font pas leur travail. Le ticket dit
« problème de permissions sur les volumes », et c'est exactement le genre de
formulation qui coûte une matinée : elle range trois pannes distinctes dans un
seul mot.

Le premier conteneur n'écrit pas dans son répertoire. Le deuxième non plus. Le
troisième n'a même pas démarré. On applique le geste réflexe, un `chmod` large
sur les trois répertoires, et **une seule des trois pannes disparaît**. Les deux
autres sont intactes, parce qu'elles n'avaient rien à voir avec les droits.

## L'objectif

Lire les messages, et les lire **mot à mot** :

```text
perm-a            n'arrive pas à écrire dans /ref
perm-b            n'arrive pas à écrire dans /donnees
perm-c            n'a pas démarré
temoin-sans-bit   n'a pas démarré non plus, pour la même raison, et vous
                  NE LE RÉPARAREZ PAS
```

Essayez vous-même les deux écritures. Le moteur ne rend pas la même phrase dans
les deux cas, et c'est toute la clé : l'une parle du **système de fichiers**,
l'autre des **droits**. La première accuse le montage, la seconde dit que le
montage est d'accord et que ce sont les droits qui refusent.

Renseignez les trois lignes de `/opt/lab-permission/reponses.txt` :

```text
rw_b=<ce que l'inspection de perm-b déclare pour son montage>
uid_b=<l'uid sous lequel perm-b tourne>
code_c=<le code de sortie de temoin-sans-bit>
```

La première réponse est celle qui porte le lab : elle prouve que la panne de
`perm-b` n'est **pas** celle de `perm-a`, alors que le symptôme se ressemble.

L'énoncé est aussi déposé dans `/opt/MISSION.md`.

## La troisième panne n'est pas une affaire de droits

`perm-c` ne démarre pas, et son code de sortie est celui du fichier **trouvé
mais non exécutable**, déjà rencontré dans le lab sur le code 127. Ici la cause
est ailleurs : le script vient d'un montage, et **un montage ne change aucun
mode**. Celui du fichier est celui de l'hôte, et il le restera.

C'est pourquoi un `chmod` joué **dans** le conteneur ne sert à rien, et pourquoi
le conteneur ne démarre de toute façon pas assez longtemps pour qu'on y joue
quoi que ce soit.

## La réparation, et c'est là que le lab a un avis

Les trois conteneurs doivent travailler : écrire pour les deux premiers, tourner
et avoir produit sa trace pour le troisième.

Mais `perm-b` doit y arriver **sans passer root**. Repasser en root réglerait le
symptôme en une option, et le contrôle le refuse expressément : le lab sur les
permissions a montré la bonne réponse, qui est d'aligner le groupe. Un lab de
dépannage ne doit pas défaire ce qu'un lab de méthode a enseigné.

## Ce qui est noté

L'**état du système**. Les trois valeurs attendues sont lues au moment de la
notation, et aucune n'est écrite dans les contrôles.

Chaque réparation est éprouvée par l'**effet** : une écriture réelle pour les
deux premières, la trace du script pour la troisième. Pas une option de ligne de
commande, qui dirait seulement ce que vous avez tapé.
