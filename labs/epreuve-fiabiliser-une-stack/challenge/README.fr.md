# Épreuve : fiabiliser une stack

La stack marche, « en relançant deux fois ». Deux services : `coffre`, qui
détient une valeur dérivée d'un mot de passe, et `api`, qui l'interroge **à son
démarrage** puis la sert.

## Les cinq contrôles

Ils sont de poids égal, et chacun porte sur un fait vérifiable.

### 1. La stack répond du premier coup, à froid

**Le contrôle démarre la stack lui-même** : c'est la seule façon de mesurer un
démarrage à froid, puisqu'une stack déjà debout a oublié comment elle s'est
levée, et que la seconde tentative réussit toujours.

Deux faits sont exigés ensemble : l'API répond, **et** aucun service n'a eu
besoin de redémarrer. Le second est le vrai contrôle : avec une politique de
redémarrage et sans attente de la santé du coffre, l'API finit par répondre,
après deux ou trois morts. Elle marche, et elle est fausse.

### 2. Le mot de passe hors de l'environnement, et pourtant arrivé

**C'est l'exigence critique : elle n'est compensée par aucun total.**

Deux faces, mesurées ensemble. Le secret ne doit plus être lisible dans
l'environnement, dans l'image, ni dans ce que rend `docker compose config`. Et
le coffre doit le recevoir **quand même** : retirer une variable sans la
remplacer donne une stack propre et fausse, et le contrôle compare la valeur
servie à celle qu'il attend.

### 3. Une limite mémoire déclarée et appliquée

`HostConfig.Memory` dit ce que le moteur a **retenu**. `memory.max` du cgroup
dit ce que le noyau **applique**. Les deux peuvent différer : une limite écrite
dans une section que le moteur n'honore pas laisse la première à zéro, et c'est
le cas classique d'une section de déploiement écrite pour un orchestrateur qui
n'est pas là.

Aucune valeur n'est imposée : une limite trop basse tuerait le service, et le
contrôle du démarrage le verrait.

### 4. Un conteneur tué repart seul

**Le contrôle tue l'API**, parce que déclarer `restart:` ne prouve rien : la
valeur peut être lue par Compose et ne jamais s'appliquer, par exemple sur un
conteneur créé avant le changement.

`docker kill` et non `docker stop` : un arrêt demandé est un arrêt voulu, et
aucune politique ne redémarre un conteneur qu'on a arrêté soi-même.

### 5. Deux variantes qui disent des choses différentes

Le contrôle lit `docker compose config`, et non les fichiers : c'est la
composition telle que le moteur la comprend, superpositions appliquées. Un
`volumes:` écrit au mauvais niveau d'indentation n'y apparaît pas, alors qu'il
est bien dans le fichier.

## Le barème

Cinq contrôles de poids égal, seuil à **75 sur 100**, et **seul l'état final
compte**.

Quatre indices, du plus vague au plus explicite, et **ils coûtent des points** :

```bash
dsoxlab hint
```
