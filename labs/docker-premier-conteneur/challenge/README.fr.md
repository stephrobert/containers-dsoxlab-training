# Trois conteneurs, trois états, et une confusion à lever

## La situation

Vous arrivez sur une machine où quelqu'un a déjà travaillé. Deux conteneurs y
sont, et ils ne sont pas dans le même état :

```text
vitrine   il tourne
rebut     il existe, arrêté
```

Ce deuxième état est celui qui déroute, et c'est le sujet de ce lab : **un
conteneur arrêté n'a pas disparu**. Il occupe encore son nom, ses journaux sont
encore lisibles, et il réapparaîtra dans toute liste qui ne se limite pas aux
conteneurs en marche. Beaucoup croient avoir fait le ménage en arrêtant, puis
butent sur un nom déjà pris sans comprendre pourquoi.

## L'objectif

Trois gestes, et rien de plus. L'image dont vous avez besoin est déjà sur la
machine : il n'y a rien à tirer d'un registre et rien à construire.

1. **Lancer** un conteneur nommé `premier`, qui **tourne**, et dont les
   journaux portent la ligne exacte `premier-est-la`.
2. **Arrêter** `vitrine`, sans le supprimer.
3. **Supprimer** `rebut`.

L'énoncé est aussi déposé sur la machine, dans `/opt/MISSION.md`.

Attention au premier geste : un conteneur dont la commande se termine s'arrête
aussitôt. « Lancé » ne suffit donc pas, il faut qu'il soit encore en marche
quand on le regarde.

## Ce qui est noté

L'**état du moteur**, jamais les commandes tapées. Un conteneur qui tourne, le
contenu de ses journaux, un conteneur arrêté qui existe encore, un nom qui a
disparu. Les deuxième et troisième gestes sont notés **séparément**, parce que
c'est exactement là que la confusion se loge.

Rien de ce lab n'a à survivre à un redémarrage : ce sont des états du moteur,
pas de la machine.

## Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service. L'image
`lab-base:1.0` est déjà présente : **rien à tirer, rien à construire**.

Deux conteneurs existent déjà, dans deux états différents :

```text
vitrine   il tourne
rebut     il existe, arrêté
```

### 1. Lancer un conteneur qui tourne

Un conteneur nommé **`premier`**, dans l'état `running` au moment du contrôle.

Le piège est immédiat : un conteneur dont la commande se termine s'arrête
aussitôt. Lancer l'image telle quelle ne suffit donc pas, il faut lui donner de
quoi rester en vie.

### 2. Ses journaux portent la ligne demandée

Exactement `premier-est-la`, dans les journaux de `premier`.

Les journaux d'un conteneur sont la **sortie de son processus principal** :
rien d'autre ne les remplit. Ce que vous demandez au conteneur d'afficher s'y
retrouve, et c'est ce qui distingue « j'ai lancé une image » de « j'ai lancé
une image en lui disant quoi faire ».

### 3. Arrêter `vitrine`, sans le supprimer

Il doit **exister encore** et ne plus tourner. Le supprimer est une faute
notée : le contrôle le dit explicitement, parce que c'est l'erreur que ce lab
existe pour lever.

Arrêter met fin au processus du conteneur en conservant le conteneur, avec ses
journaux et son nom.

### 4. Supprimer `rebut`

Son nom doit avoir disparu de la liste, celle qui montre **aussi** les
conteneurs arrêtés.

C'est la conséquence observable d'une suppression, et c'est aussi pourquoi un
conteneur arrêté gêne : tant qu'il existe, il garde son nom, et aucun autre
conteneur ne peut le reprendre.

### Ce qui n'est pas noté

La commande que vous avez tapée. Un conteneur peut être lancé de dix façons, et
un arrêt peut venir d'un `stop`, d'un signal ou d'un `kill` : le contrôle
regarde l'état obtenu, pas le chemin.
