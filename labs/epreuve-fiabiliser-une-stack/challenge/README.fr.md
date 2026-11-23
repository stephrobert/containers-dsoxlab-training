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

## Épreuve : fiabiliser une stack

La stack marche, « en relançant deux fois ». Deux services : `coffre`, qui
détient une valeur dérivée d'un mot de passe, et `api`, qui l'interroge **à son
démarrage** puis la sert.

### Les cinq contrôles

Ils sont de poids égal, et chacun porte sur un fait vérifiable.

#### 1. La stack répond du premier coup, à froid

**Le contrôle démarre la stack lui-même** : c'est la seule façon de mesurer un
démarrage à froid, puisqu'une stack déjà debout a oublié comment elle s'est
levée, et que la seconde tentative réussit toujours.

Deux faits sont exigés ensemble : l'API répond, **et** aucun service n'a eu
besoin de redémarrer. Le second est le vrai contrôle : une stack qui se rattrape
toute seule finit par répondre, et elle marche alors par accident.

#### 2. Le mot de passe hors de l'environnement, et pourtant arrivé

**C'est l'exigence critique : elle n'est compensée par aucun total.**

Deux faces, mesurées ensemble. Le secret ne doit plus être lisible dans
l'environnement, dans l'image, ni dans ce que rend `docker compose config`. Et
le coffre doit le recevoir **quand même** : retirer une variable sans la
remplacer donne une stack propre et fausse, et le contrôle compare la valeur
servie à celle qu'il attend.

#### 3. Une limite mémoire déclarée et appliquée

`HostConfig.Memory` dit ce que le moteur a **retenu** de la déclaration.
`memory.max` du cgroup dit ce que le noyau **applique**. Les deux sont lus parce
que ce sont deux faits distincts, et que seul le second protège l'hôte : une
déclaration que le moteur accepte sans un mot peut n'imposer **aucune** limite
au conteneur.

Aucune valeur n'est imposée : une limite trop basse tuerait le service, et le
contrôle du démarrage le verrait.

#### 4. Un service qui meurt repart seul

**Chaque service** porte une politique de redémarrage, le coffre comme l'API :
une stack dont le coffre ne repart pas n'est pas fiabilisée, puisque l'API tombe
avec lui. Le contrôle lit la politique des deux.

**Et il fait mourir l'API**, parce que déclarer `restart:` ne prouve rien : la
valeur peut être lue par Compose et ne jamais s'appliquer, par exemple sur un
conteneur créé avant le changement.

Il la fait mourir par le **déclencheur de panne** que le scénario annonce, et
non par un `docker kill` : le moteur traite un arrêt demandé de l'extérieur
comme un arrêt voulu, et aucune politique ne relance un conteneur arrêté ainsi.
Ce qu'une politique couvre est un processus qui meurt de lui-même.

#### 5. Deux variantes qui disent des choses différentes

Le contrôle lit `docker compose config`, et non les fichiers : c'est la
composition telle que le moteur la comprend, superpositions appliquées. Un
`volumes:` écrit au mauvais niveau d'indentation n'y apparaît pas, alors qu'il
est bien dans le fichier.

### Le barème

Cinq contrôles de poids égal, seuil à **75 sur 100**, et **seul l'état final
compte**.

Quatre indices, du plus vague au plus explicite, et **ils coûtent des points** :

```bash
dsoxlab hint
```
