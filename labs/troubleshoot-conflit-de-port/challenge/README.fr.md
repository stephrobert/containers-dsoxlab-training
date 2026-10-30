# Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service. **Trois conteneurs
ont refusé de démarrer**, chacun sur un port déjà pris :

```text
intrus-a        voulait le port 18200 de l'hôte
intrus-b        voulait le port 18201 de l'hôte
temoin-refuse   voulait le port 18200 lui aussi
```

**Commencez par comparer les deux messages d'erreur** que le moteur a rendus
pour `intrus-a` et `intrus-b`. Ils ne disent pas la même chose, et c'est toute
la clé du diagnostic.

Les trois premières réponses vont dans `/opt/lab-conflit/reponses.txt`, une
ligne par entrée, sans espace autour du signe égal.

## 1. Le statut de `temoin-refuse`

À la ligne `statut_intrus=`.

Un conteneur refusé est **créé quand même**, et il occupe donc son nom. C'est
pourquoi un second essai échoue sur un message tout différent, qui parle de nom
déjà pris, et fait chercher un second problème qui n'existe pas.

**Ne réparez pas `temoin-refuse`** : il reste en l'état pour que son statut soit
lisible jusqu'au bout.

## 2. Le conteneur qui occupe le port 18200

À la ligne `coupable_a=`.

Le message du moteur dit que le port est **déjà alloué**. Cette formulation
signifie que c'est **lui** qui l'a réservé, donc que le coupable est un de ses
conteneurs. La liste des conteneurs le nomme aussitôt.

C'est le cas facile.

## 3. Le programme qui occupe le port 18201

À la ligne `coupable_b=`.

Le second message ne parle pas d'allocation : il parle d'une **écoute refusée**.
Cette formulation vient du système, pas du moteur, et elle dit que le coupable
est **hors** de Docker.

**Ne cherchez pas du côté de Docker** : il ne montre rien du tout ici, et c'est
précisément ce qui fait perdre du temps. La table des sockets de l'hôte nomme le
programme en une ligne.

Il faut être root pour qu'elle le nomme.

## 4. Réparez, sans rien couper

Les conteneurs `intrus-a` et `intrus-b` doivent **tourner**, et publier leur
port 80 sur un port de l'hôte **autre** que celui qui était pris.

Et les deux coupables doivent être **toujours là** : le conteneur qui tourne, et
le programme de l'hôte qui écoute.

Libérer le port serait le geste spontané, et c'est le mauvais. **Rien ne disait
qu'ils étaient inutiles**, et un port pris l'est souvent pour une raison. On ne
coupe pas un service qui tourne pour en démarrer un autre : c'est le nouveau
venu qu'on déplace.

Le contrôle vérifie les deux moitiés.

## Un détail qui n'est pas un conflit

Deux conteneurs peuvent publier le même port **de conteneur** sur deux ports
d'hôte différents. C'est le port de l'**hôte** qui est unique, pas celui du
conteneur.

## Ce qui n'est pas noté

La commande que vous avez tapée. Les coupables se trouvent de plusieurs façons,
et le déplacement se fait en recréant le conteneur sur un port libre, par
n'importe quel moyen.
