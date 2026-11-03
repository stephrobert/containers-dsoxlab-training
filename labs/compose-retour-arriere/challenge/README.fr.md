# Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable. Dans `/opt/lab-retour`, une pile
Compose **tourne déjà** : un service épinglé par digest, un volume de données,
et un enregistrement que la production a écrit avant votre arrivée.

Trois releases du même service vous sont données par leur digest, dans
`/opt/lab-retour/releases.json`. Elles ne diffèrent que par ce qu'elles savent
lire :

| release | schéma lu | ce qu'elle fait |
| --- | --- | --- |
| `1.0` | 1 | celle qui tourne |
| `2.0` | 1 | une évolution compatible |
| `3.0` | 2 | elle **migre** le schéma |

Le service écoute sur `127.0.0.1:18080`. `GET /etat` rend la release, le schéma
et les enregistrements ; `POST /ecrire` avec une valeur dans le corps en ajoute
un.

**La pile tourne dans le projet Compose `dsoxlab-retour`**, et son `compose.yaml`
ne le déclare pas. Chaque commande Compose doit donc le désigner, sans quoi vous
en créez un second, nommé d'après votre répertoire : il recevra un volume
**neuf et vide**, le service repartira d'un état vierge, et l'enregistrement
témoin aura disparu. Rien ne vous le dira.

## 1. Déployer la 2.0, par son digest

Faites passer la pile en `2.0`, **par le digest** et non par une étiquette. Une
étiquette ne dit pas ce qui tourne, un digest le dit.

Le volume de données ne change pas : l'enregistrement d'avant doit toujours être
là après la bascule.

## 2. Écrire sous la 2.0, puis revenir à la 1.0 sans rien perdre

Ajoutez un enregistrement pendant que la `2.0` tourne, puis **revenez à la 1.0**.

Les deux enregistrements, celui d'avant votre arrivée et le vôtre, doivent
survivre à l'aller comme au retour. C'est tout l'intérêt d'un retour en arrière :
il ramène le code, pas les données.

## 3. Déployer la 3.0, et mesurer ce que cela coûte

Faites passer la pile en `3.0`. Elle **migre** l'état en schéma 2, et le dit
dans son journal.

Les deux enregistrements doivent encore y être, sous leur forme migrée.

## 4. Établir que le retour en arrière n'est plus possible

Essayez de revenir à la `2.0`. Elle **refuse**, et c'est le bon comportement :
une release ne doit pas abîmer un état qu'elle ne comprend pas.

Consignez ce que vous avez mesuré dans `/opt/lab-retour/constat.txt`, une ligne
par entrée, sans espace autour du signe égal :

```text
release_qui_refuse=<la release qui s'arrete>
schema_illisible=<le numero de schema qu'elle ne sait pas lire>
code_de_sortie=<le code que son processus rend>
```

Les trois valeurs se lisent sur la machine, et aucune ne se devine. Le message
de refus en nomme **deux**, la release et le schéma. Le **code de sortie**, lui,
n'est pas dans le message et n'a aucune raison d'y être : un processus ne
s'annonce pas son propre code, il le rend. C'est au shell qu'on le demande.

## L'état final attendu

La `3.0` tourne, l'état est en schéma 2, les deux enregistrements y sont, et le
constat est rempli. C'est cet état qui est noté, pas le chemin suivi.

## Ce qui n'est pas noté

Les commandes que vous avez tapées, ni l'ordre dans lequel vous avez essayé.
Un retour en arrière se fait de plusieurs façons, et le refus de la `2.0` se
constate de plusieurs façons aussi.
