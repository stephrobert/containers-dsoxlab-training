# Durcir un service sans le casser

Le service `service-expose` tourne avec tous les droits que Docker accorde par
défaut. Son secret se lit dans son environnement. Sa racine est inscriptible. Et
depuis une mise à jour du pare-feu, il ne joint plus le fournisseur
`fournisseur-tiers`.

On vous demande de le durcir. Sans le casser.

## Ce qui est attendu à la fin

1. Le service a perdu **toutes ses capabilities sauf celle qui lui est
   nécessaire**, il porte **`no-new-privileges`**, et il **répond** toujours.
2. Sa racine est en **lecture seule**, ses écritures passent par un chemin
   déclaré, tmpfs ou volume, et une écriture ailleurs est **refusée**.
3. Le secret n'apparaît **ni dans l'environnement** du conteneur **ni dans
   l'image**, et le service le reçoit quand même : sa réponse doit rester la
   bonne. Le fichier `/opt/lab-durcir/jeton` est fourni.
4. Le flux vers le fournisseur **aboutit**, sur `127.0.0.1:19443`, le pare-feu
   reste **actif**, et sa **règle de protection** reste en place.
5. Le volume `dsoxlab-durcir-donnees` est remonté et **sa donnée est servie** ;
   les deux volumes `dsoxlab-durcir-jetable-1` et `dsoxlab-durcir-jetable-2`
   sont retirés.

L'énoncé complet est aussi sur la machine, dans `/opt/lab-durcir/MISSION.md`.

## Deux faits mesurés sur ce moteur

Ils sont donnés pour que vous ne cherchiez pas au mauvais endroit.

**`NET_BIND_SERVICE` ne sert à rien ici.** Un conteneur **sans aucune
capability** écoute très bien sur le port 80, parce que le démon pose
`net.ipv4.ip_unprivileged_port_start = 0` dans le conteneur : tous les ports y
sont « non privilégiés ». Le conseil répandu « tout retirer sauf
NET_BIND_SERVICE » ne retire donc rien d'utile et n'ajoute rien. La capability
nécessaire est ailleurs, et **les journaux du service disent quel geste échoue
quand elle manque**.

**Le pare-feu se corrige sans être désactivé**, et sans que sa table soit
supprimée. Dans une chaîne, une règle qui autorise peut primer sur une règle qui
bloque, selon leur **ordre**.

## Ce que vous n'avez pas à écrire

L'image `lab-durcir:1.0` est fournie : il n'y a **rien à reconstruire**. Le
service lit son secret dans un **fichier** avant de regarder son environnement,
et le chemin se règle par `SECRET_FICHIER`, dont le défaut est
`/run/secrets/jeton`. Son répertoire de travail se règle par `TRAVAIL`, dont le
défaut est `/travail`.

seccomp et AppArmor ne sont pas mesurés par cette épreuve.

## Comment vous êtes noté

Cinq contrôles de poids égal, et **seul l'état final compte**.

Le seuil est de **75 sur 100**, et cette épreuve porte **deux** exigences que
rien ne compense :

- **le secret lisible dans l'environnement** ;
- **le pare-feu désactivé**, ou sa table supprimée, ou sa règle de protection
  retirée.

Les deux sont des portes ouvertes, et une porte ouverte ne se compense pas par du
travail fait ailleurs. La seconde est la fausse correction la plus tentante de
toute l'épreuve : le flux ne passe pas, le pare-feu bloque, donc on retire le
pare-feu. Le symptôme disparaît en une commande, et la machine est nue.

Quatre indices sont disponibles, et **ils coûtent des points** : `dsoxlab hint`.

## Épreuve : durcir sans casser

Le service tourne avec tous les droits par défaut, son secret est dans son
environnement, sa racine est inscriptible, et il ne joint plus son fournisseur.

### Les cinq contrôles

Ils sont de poids égal, et chacun porte sur un fait vérifiable.

#### 1. Les droits retirés, et le service qui répond encore

**Trois faits** : le jeu de capabilities est réduit, `no-new-privileges` est
posé, et le service répond. Le troisième distingue cette épreuve d'un exercice de
suppression : tout retirer est facile, et le service meurt.

Le contrôle **n'impose aucune capability par son nom**. Il mesure que le jeu est
réduit et que le service tourne : un apprenant qui trouve un autre chemin pour se
passer de la capability a mieux durci, et l'épreuve ne doit pas le punir.

#### 2. La racine en lecture seule, et les écritures déclarées

Deux faits qui n'ont de sens qu'ensemble : une racine en lecture seule sans
chemin d'écriture déclaré donne un service qui meurt, et un chemin déclaré sans
racine en lecture seule ne protège rien.

Le contrôle les mesure **en faisant** : une écriture hors des chemins déclarés
doit être refusée. Lire `ReadonlyRootfs` ne suffirait pas, car le drapeau dit
l'intention et l'essai dit le résultat.

#### 3. Le secret hors de l'environnement, et pourtant arrivé

**Première exigence critique.** Deux faces : le secret a disparu de
l'environnement et de l'image, **et** le service le reçoit. Retirer une variable
sans la remplacer donne un service propre et faux, et le contrôle compare la
valeur servie à celle qu'il attend.

#### 4. Le flux rétabli, le pare-feu intact

**Seconde exigence critique**, et la fausse correction la plus tentante de
l'épreuve : retirer le pare-feu fait disparaître le symptôme en une commande et
laisse la machine nue.

Trois faits mesurés ensemble : le flux aboutit, la table existe toujours, et la
protection **protège encore**. Le troisième est le plus fin : une correction qui
vide la chaîne lève le blocage **et** la protection, ce qui ressemble à un travail
fait. Le contrôle ne se contente donc pas de lire la règle, il vérifie qu'elle
agit.

#### 5. Le volume utile servi, les jetables retirés

Le durcissement passe par une recréation du conteneur, et c'est là qu'un volume
s'oublie. Trois volumes portent le nom du lab : un seul compte, et l'énoncé dit
lequel.

Le contrôle lit **la donnée servie**, et non la seule existence du volume : un
volume remonté vide porte le bon nom et ne vaut rien.

### Le barème

Cinq contrôles de poids égal, seuil à **75 sur 100**, et **deux** exigences
critiques.

Quatre indices, du plus vague au plus explicite, et **ils coûtent des points** :

```bash
dsoxlab hint
```
