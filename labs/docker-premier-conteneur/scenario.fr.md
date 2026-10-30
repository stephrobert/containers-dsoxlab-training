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
