# Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service. L'image
`lab-base:1.0` est déjà présente : **rien à tirer, rien à construire**.

Deux conteneurs existent déjà, dans deux états différents :

```text
vitrine   il tourne
rebut     il existe, arrêté
```

## 1. Lancer un conteneur qui tourne

Un conteneur nommé **`premier`**, dans l'état `running` au moment du contrôle.

Le piège est immédiat : un conteneur dont la commande se termine s'arrête
aussitôt. Lancer l'image telle quelle ne suffit donc pas, il faut lui donner de
quoi rester en vie.

## 2. Ses journaux portent la ligne demandée

Exactement `premier-est-la`, dans les journaux de `premier`.

Les journaux d'un conteneur sont la **sortie de son processus principal** :
rien d'autre ne les remplit. Ce que vous demandez au conteneur d'afficher s'y
retrouve, et c'est ce qui distingue « j'ai lancé une image » de « j'ai lancé
une image en lui disant quoi faire ».

## 3. Arrêter `vitrine`, sans le supprimer

Il doit **exister encore** et ne plus tourner. Le supprimer est une faute
notée : le contrôle le dit explicitement, parce que c'est l'erreur que ce lab
existe pour lever.

Arrêter met fin au processus du conteneur en conservant le conteneur, avec ses
journaux et son nom.

## 4. Supprimer `rebut`

Son nom doit avoir disparu de la liste, celle qui montre **aussi** les
conteneurs arrêtés.

C'est la conséquence observable d'une suppression, et c'est aussi pourquoi un
conteneur arrêté gêne : tant qu'il existe, il garde son nom, et aucun autre
conteneur ne peut le reprendre.

## Ce qui n'est pas noté

La commande que vous avez tapée. Un conteneur peut être lancé de dix façons, et
un arrêt peut venir d'un `stop`, d'un signal ou d'un `kill` : le contrôle
regarde l'état obtenu, pas le chemin.
