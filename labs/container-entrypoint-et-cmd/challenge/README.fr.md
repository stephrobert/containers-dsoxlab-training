# Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service. Deux images sont
déjà construites, et **leurs Dockerfile sont lisibles** dans
`/opt/lab-entrypoint` : lisez-les, c'est la moitié de l'exercice.

```text
img-cmd:1.0          déclare seulement un CMD
img-entrypoint:1.0   déclare un ENTRYPOINT et un CMD
```

Quatre conteneurs à produire, et **aucun `--rm`** : c'est dans les journaux
qu'on lit ce qui a tourné.

## 1. `defaut` : le point de référence

Depuis `img-cmd:1.0`, **sans argument**. Ses journaux doivent porter
`defaut-de-limage`.

Un `CMD` est ce que l'image exécute quand on ne lui demande rien. Rien d'autre
n'est noté ici : c'est la référence à laquelle les trois suivants se comparent.

## 2. `remplace` : un CMD ne résiste pas

Depuis `img-cmd:1.0`, ses journaux doivent porter `remplacement-total`, et
**pas** `defaut-de-limage`.

Ce qu'on passe après le nom de l'image prend la place du `CMD`, **entièrement**.
C'est une commande qui est attendue là, pas un simple mot : si vous ne passez
qu'un texte, le conteneur essaiera de l'exécuter.

L'absence du défaut est aussi notée que la présence de votre texte : c'est elle
qui prouve le remplacement.

## 3. `complete` : un ENTRYPOINT, lui, résiste

Depuis `img-entrypoint:1.0`, ses journaux doivent porter le préfixe de
l'entrypoint **et** `complement-cmd`.

Le même geste qu'au point 2 ne produit plus le même effet : l'argument ne
remplace plus rien, il devient l'argument de l'entrypoint, en prenant la place
du `CMD`. C'est le point qui surprend, et c'est tout le sujet du lab.

## 4. `contourne` : la règle a une porte de sortie

Depuis `img-entrypoint:1.0`, ses journaux doivent porter `sans-prefixe` et
**pas** le préfixe.

Un `ENTRYPOINT` se remplace, mais seulement par l'**option prévue pour cela**.
Passer un argument ne suffit pas : vous retomberiez sur le cas 3. C'est ce qui
le distingue d'un `CMD` : le contournement est un geste délibéré, pas un effet
de bord.

## Ce qui n'est pas noté

La commande que vous avez tapée, ni la forme que vous employez. Deux des quatre
résultats s'obtiennent aussi bien en forme exec qu'en forme shell, et les deux
comptent.
