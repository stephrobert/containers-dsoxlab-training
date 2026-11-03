# La stack qui ne marche qu'à la deuxième tentative

Cette stack tourne depuis des mois, et l'équipe a pris une habitude : quand elle
ne répond pas, on la relance. Ça marche. Personne n'a cherché pourquoi.

Elle est dans `/opt/lab-stack-fiable/compose.yaml`, son projet se nomme
`stack-fiable`, et elle a deux services. `coffre` détient une valeur dérivée
d'un mot de passe. `api` l'interroge **à son démarrage**, puis la sert sur
`127.0.0.1:18420`.

Trois autres choses ont été relevées en passant, et aucune n'a l'air urgente :
le mot de passe se lit dans le fichier, aucun service n'a de limite, et le
montage du code source qui servait en développement est encore là.

## Ce qui est attendu à la fin

1. Un `docker compose down` suivi d'un `docker compose up -d` rend une stack
   qui **répond du premier coup**, sans qu'aucun service ait eu besoin de
   redémarrer.
2. Le mot de passe n'apparaît **ni dans l'environnement** des conteneurs, **ni
   dans l'image**, ni dans ce que rend `docker compose config`, et le coffre le
   reçoit quand même : la valeur servie doit rester la bonne.
3. Chaque service porte une **limite mémoire**, visible dans l'inspection du
   conteneur comme dans son cgroup.
4. Chaque service porte une **politique de redémarrage** : un conteneur tué
   repart seul.
5. Il existe **deux variantes** : `compose.yaml`, le déploiement, qui ne monte
   **pas** le code source, et `compose.dev.yaml`, le développement, qui le
   monte. La seconde se superpose à la première.

Le projet garde son nom, et l'API garde son port. L'image `lab-stack-fiable:1.0`
est fournie : il n'y a **rien à reconstruire**.

Le service porte un **déclencheur de panne**, qui est un outil du lab et non une
énigme : si le fichier `/tmp/panne-provoquee` existe dans un conteneur, le
service en sort en erreur dès la requête suivante. C'est ainsi que le contrôle
de la politique de redémarrage fait mourir un service, parce qu'un `docker kill`
ne le ferait pas : le moteur le traite comme un arrêt voulu, et aucune politique
ne relance un conteneur qu'on a arrêté soi-même.

L'énoncé complet est aussi sur la machine, dans
`/opt/lab-stack-fiable/MISSION.md`. Il précise notamment que le service lit son
mot de passe dans un **fichier** avant de regarder son environnement, et que le
chemin de ce fichier se règle par une variable.

## Comment vous êtes noté

Cinq contrôles de poids égal, et **seul l'état final compte**. Aucune syntaxe
n'est imposée : deux façons d'obtenir le même comportement reçoivent la même
note.

Le seuil est de **75 sur 100**. Une exigence ne se compense par aucun total :
**un mot de passe lisible fait échouer l'épreuve**, même avec tout le reste en
place. Et il est cherché à **quatre** endroits, pas un : l'environnement des
conteneurs, les **couches de l'image**, ce que rend `docker compose config`, et
la **valeur servie** par l'API.

Le sortir de l'environnement pour le mettre dans l'image n'est donc pas une
correction, c'est une aggravation : une variable se lit par `docker inspect` et
par quiconque parle au démon, mais une image **se publie**.

Attention à la fausse correction : retirer le mot de passe **sans le remplacer**
donne une stack propre et fausse. Le contrôle compare la valeur servie à celle
qu'il attend.

Quatre indices sont disponibles, et **ils coûtent des points** : `dsoxlab hint`.
