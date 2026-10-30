# Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service. Deux conteneurs
**tournent déjà** et partagent le volume `rapports-partages`, monté sur
`/rapports`.

L'image `lab-permissions:1.0` porte deux comptes dans le **même groupe** :

```text
redacteur       uid 1000, groupe equipe (gid 2000)
verificateur    uid 1001, groupe equipe (gid 2000)
```

État actuel, qui est le résultat de deux mauvaises réponses :

```text
rapport        tourne en ROOT, parce que sinon il n'écrivait pas
verificateur   tourne en non-root, et il n'écrit rien
```

## 1. `rapport` ne tourne plus en root

Son uid doit être non nul, et son gid doit être celui du groupe partagé.

L'identité est lue **dans** le conteneur, pas dans ce qui a été demandé à la
création : c'est elle qui décide des droits.

## 2. Ce que `rapport` écrit lui appartient

Un fichier qu'il écrit dans `/rapports` doit lui appartenir **et** porter le
groupe partagé.

Les deux ne se séparent pas : pouvoir écrire sans que le fichier porte le bon
groupe donnerait un volume où chacun produit des fichiers que les autres ne
peuvent pas reprendre. C'est la panne suivante, et elle est pire parce qu'elle
arrive plus tard.

## 3. Le répertoire appartient au groupe partagé, en écriture

`/rapports` doit appartenir au groupe partagé et lui donner l'**écriture**.

Le propriétaire peut très bien rester root : ce n'est pas lui qui donne le droit
d'écrire ici.

## 4. L'autre uid écrit, et le volume n'est pas ouvert à tous

`verificateur`, dont l'uid est **différent**, doit écrire aussi dans
`/rapports`. Et le répertoire ne doit **pas** être ouvert en écriture à tout le
monde.

Les deux moitiés sont indissociables. `chmod 777` ferait passer les trois
contrôles précédents : il marche, et il donne à n'importe quel processus du
conteneur le droit de tout réécrire.

Ne touchez pas à `verificateur` : c'est le témoin du groupe partagé. Lui donner
le même uid que `rapport` ne prouverait rien, puisque tout l'intérêt est que
deux uid différents travaillent côte à côte.

## Deux choses à savoir avant de commencer

**L'utilisateur d'un conteneur se fixe à sa création** : il faut le recréer.
C'est la même règle que pour les montages, les ports publiés et le réseau.

Et **on ne peut pas écrire dans un volume sans un conteneur qui le monte**. Pour
changer ses droits, lancez-en un jetable qui le monte, avec les privilèges qu'il
faut.

## Un conseil d'ordre

Réglez les droits du volume **avant** de recréer le conteneur sous son compte.
L'inverse donne un conteneur qui n'écrit pas, et vous conclurez à tort que le
compte est le problème.

## Ce qui n'est pas noté

La commande que vous avez tapée. Les droits du volume se changent de plusieurs
façons. Mais l'état est mesuré par l'**écriture réelle**, pas seulement par la
lecture des permissions : une permission se déclare sans toujours produire
l'effet attendu.
