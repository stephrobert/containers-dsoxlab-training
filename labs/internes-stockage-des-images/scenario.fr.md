# Le disque est plein, et aucun volume n'est en cause

## La situation

Le serveur alerte : la partition qui porte `/var` est à 96 %. Vous cherchez le
coupable dans les volumes, puisque c'est là que les données vivent. Ils pèsent
quelques centaines de mégaoctets en tout.

Vous cherchez dans les images. Elles sont nombreuses, mais le compte ne tombe
pas non plus.

Ce qui remplit le disque, ce sont les conteneurs eux-mêmes. Pas leurs volumes :
**eux**. Chacun a une couche d'écriture à lui, qui reçoit tout ce qu'il écrit
hors d'un volume, et cette couche est un répertoire ordinaire de votre disque.
Un service qui journalise dans un fichier au lieu de sa sortie standard la
remplit tranquillement, pendant des mois.

## L'objectif

Aller voir cet endroit, et constater qu'il n'a rien de mystérieux. Le conteneur
`entrepot` tourne, et il n'a encore rien écrit.

Renseignez les deux lignes de `/opt/lab-stockage/reponses.txt` :

```text
pilote=<le pilote de stockage que le moteur emploie>
ecriture=<le chemin ABSOLU de la couche d'ÉCRITURE de `entrepot`, sur l'hôte>
```

Puis, **depuis le conteneur**, faites deux choses :

1. écrivez dans `/trace-ecriture.txt` la ligne
   `ceci-a-ete-ecrit-dans-le-conteneur` ;
2. créez un fichier `/charge.bin` de 5 Mo.

Les deux doivent se retrouver sur le **disque de l'hôte**, dans la couche
d'écriture.

L'énoncé est aussi déposé dans `/opt/MISSION.md`.

## Ce que vous allez constater

Que le fichier écrit dans le conteneur se lit depuis l'hôte **immédiatement**,
sans export ni commande particulière. Un conteneur n'écrit pas dans un ailleurs.

Et que la couche ne contient **que les différences** : après une écriture, elle
ne porte que ce fichier, pas une copie du système de fichiers. C'est ce qui rend
les conteneurs légers, et c'est aussi ce qui fait qu'ils grossissent sans qu'on
les voie grossir.

## Ce qui est noté

L'**état du système**, et la quatrième mesure est une **pesée** : la couche doit
peser au moins ce que vous y avez écrit. C'est la conséquence qui compte en
exploitation, et celle qu'on découvre trop tard.

Un fichier créé dans un volume ou en mémoire n'apparaîtrait pas là, et c'est
précisément la différence que les labs sur les volumes ont enseignée.

## Une précision d'outillage

`/var/lib/docker` n'est pas lisible par un compte ordinaire. Il faut être root
pour regarder, c'est normal, et ce n'est pas le sujet du lab.

Attention aussi au choix du fichier de charge : un fichier **alloué** sans être
écrit peut n'occuper aucun bloc sur le disque, et la pesée le compterait pour
zéro. Écrivez de vrais octets.
