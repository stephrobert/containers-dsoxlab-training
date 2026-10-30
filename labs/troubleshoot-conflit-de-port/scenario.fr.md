# Deux conteneurs refusent de démarrer, pour deux raisons

## La situation

Un déploiement échoue. Deux services ne démarrent pas, et les deux messages
parlent de port. On relance, ça échoue pareil. On relance encore, et là le
message **change** : il parle maintenant d'un nom déjà utilisé.

On croit avoir cassé autre chose entre-temps. On passe vingt minutes sur le
mauvais problème.

Puis on cherche le coupable du premier port, et on le trouve en une commande.
On cherche celui du second de la même façon, et **il n'y a rien**. La liste des
conteneurs est muette, et le port est pourtant bien pris.

## L'objectif

Faire parler les deux messages. Deux conteneurs ont refusé de démarrer, chacun
sur un port déjà pris, et un troisième est là pour servir de témoin :

```text
intrus-a        voulait le port 18200 de l'hôte
intrus-b        voulait le port 18201 de l'hôte
temoin-refuse   voulait le port 18200 lui aussi, et vous NE LE RÉPARAREZ PAS
```

**Comparez les deux messages d'erreur** que le moteur a rendus pour `intrus-a`
et `intrus-b`. Ils ne disent pas la même chose, et c'est toute la clé du
diagnostic : l'un vient du moteur, qui sait ce qu'il a déjà réservé, l'autre
vient du système, qui refuse l'écoute.

Renseignez les trois lignes de `/opt/lab-conflit/reponses.txt` :

```text
statut_intrus=<le STATUT de temoin-refuse, tel que le moteur le déclare>
coupable_a=<le NOM du conteneur qui occupe le port 18200>
coupable_b=<le NOM DU PROGRAMME qui occupe le port 18201>
```

Pour la troisième, **ne cherchez pas du côté de Docker** : il ne montre rien, et
c'est précisément ce qui fait perdre du temps. Un outil système le nomme en une
ligne.

L'énoncé est aussi déposé dans `/opt/MISSION.md`.

## La première question explique le message qui change

Un conteneur refusé est **créé quand même**. Son statut le dit, et il occupe
donc son nom.

C'est pourquoi le second essai échoue sur un message tout différent, qui parle
de nom déjà pris : deux messages pour une seule cause, et on cherche deux
problèmes. Les vingt minutes du scénario sont là.

## La réparation, et c'est là que le lab a un avis

Les deux conteneurs doivent **tourner**, et publier leur port 80 sur un port de
l'hôte **autre** que celui qui était pris.

Et les deux coupables doivent être **toujours là** : le conteneur qui tourne, et
le programme de l'hôte qui écoute.

Libérer le port serait le geste spontané, et c'est le mauvais. **Rien ne disait
qu'ils étaient inutiles**, et un port pris l'est souvent pour une raison. On ne
coupe pas un service qui tourne pour en démarrer un autre : c'est le nouveau
venu qu'on déplace.

## Ce qui est noté

L'**état du système**. Les trois valeurs attendues sont lues au moment de la
notation, et aucune n'est écrite dans les contrôles.

Le quatrième contrôle vérifie les deux moitiés de la réparation : que les
intrus tournent **ailleurs**, et que les coupables sont intacts. Sans la seconde,
la réponse la plus destructrice passerait, et le lab enseignerait exactement ce
qu'il faut éviter.
