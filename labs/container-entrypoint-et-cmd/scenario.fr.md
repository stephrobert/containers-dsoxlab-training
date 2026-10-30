# L'argument est passé, et il n'a pas eu le même effet

## La situation

Une équipe livre deux images qui font le même travail. Sur la première, passer
un argument à `docker run` change la commande exécutée. Sur la seconde, le même
argument ne remplace rien : il s'ajoute à ce qui tournait déjà.

Personne ne comprend pourquoi, et la discussion tourne autour de l'idée qu'une
des deux images serait « mal faite ». Les deux sont correctes. Elles ne
déclarent simplement pas leur commande de la même façon, et cette différence ne
se voit pas en regardant l'image : elle se voit dans ce qui arrive quand on lui
passe quelque chose.

Deux règles suffisent à tout expliquer. Ce lab ne vous les énonce pas : il vous
fait produire les quatre situations où elles se manifestent.

## L'objectif

Les deux images sont déjà construites sur la machine, et **leurs Dockerfile
sont lisibles** dans `/opt/lab-entrypoint` :

```text
img-cmd:1.0          déclare seulement un CMD
img-entrypoint:1.0   déclare un ENTRYPOINT et un CMD
```

Produisez quatre conteneurs. Chacun doit **rester** : c'est dans ses journaux
qu'on lit ce qui a tourné, et un `--rm` effacerait la preuve.

| Conteneur | Depuis | Ce que ses journaux doivent montrer |
| --- | --- | --- |
| `defaut` | `img-cmd:1.0`, sans argument | `defaut-de-limage` |
| `remplace` | `img-cmd:1.0` | `remplacement-total`, **à la place** du défaut |
| `complete` | `img-entrypoint:1.0` | le préfixe de l'entrypoint **et** `complement-cmd` |
| `contourne` | `img-entrypoint:1.0` | `sans-prefixe`, **sans** le préfixe |

L'énoncé est aussi déposé dans `/opt/MISSION.md`.

## Ce qui est noté

Ce qui s'est **exécuté**, lu dans les journaux des quatre conteneurs. Pas ce
que les images déclarent : cela, le setup l'a écrit, et le vérifier ne vous
apprendrait rien.

Chaque contrôle vérifie aussi une **absence**, et c'est ce qui le rend
sérieux : un conteneur dont les journaux portent à la fois le défaut et votre
texte n'a rien remplacé, et un conteneur qui garde le préfixe n'a rien
contourné.
