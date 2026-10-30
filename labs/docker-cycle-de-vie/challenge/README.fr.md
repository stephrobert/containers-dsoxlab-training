# Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service. L'image
`lab-cycle:1.0` est déjà présente : **rien à tirer, rien à construire**.

```text
dormeur   ARRÊTÉ, il porte /empreinte.txt
actif     il TOURNE
```

## 1. `dormeur` tourne à nouveau, et c'est le MÊME conteneur

Son identifiant ne doit pas avoir changé. Celui d'origine a été relevé avant
votre arrivée, dans `/opt/lab-cycle/id-dormeur.txt` : vous pouvez comparer
vous-même avec celui que le moteur affiche aujourd'hui.

Le relancer en le recréant sous le même nom **ne compte pas**. Les deux gestes
donnent un conteneur qui tourne, et c'est exactement ce qui rend la confusion
durable : seule l'empreinte les sépare.

## 2. Son fichier `/empreinte.txt` est toujours là

C'est la conséquence observable du point précédent, et il n'y a rien à faire de
plus pour l'obtenir : un conteneur redémarré l'a encore, un conteneur recréé est
vierge.

Si ce contrôle refuse alors que vous croyez avoir redémarré, c'est la réponse à
votre question.

## 3. `actif` est en pause

Ni arrêté, ni supprimé : **en pause**. C'est un troisième état, que la mise en
pause gèle sans terminer les processus, et il se défait.

Un conteneur en pause n'est ni en marche ni arrêté. C'est pour cela qu'il figure
dans ce lab : le cycle de vie n'est pas une ligne, c'est un graphe.

## 4. Un conteneur `sortie` est terminé, avec le code 42

Il doit avoir **tourné** puis s'être **terminé**, et porter le code de sortie
`42`.

Le code est celui que rend le processus principal du conteneur, et il **survit
au conteneur** : c'est ce qu'un orchestrateur lit pour décider de relancer ou
d'alerter. Un conteneur encore en marche n'en porte aucun.

## Ce qui n'est pas noté

La commande que vous avez tapée. Un conteneur arrêté se redémarre de plusieurs
façons, et la mise en pause aussi : le contrôle regarde l'état et l'identité,
pas le chemin.
