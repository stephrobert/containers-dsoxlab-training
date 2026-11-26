# Un service, et pas plus de seize tâches

## La situation

Le service `worker` peut créer jusqu'à 32 tâches. Son budget d'exploitation est
de 16. Vous devez l'y ramener sans perdre ses autres limites, et vérifier qu'une
rafale de processus est refusée sans emporter le service.

## Mission

Sur `docker.lab`, le projet Compose est dans
`/opt/dsoxlab-container-limite-de-processus`, sous le nom
`dsoxlab-container-limite-de-processus`. Gardez un seul `worker` en marche, avec
son label `dsoxlab.lab=container-limite-de-processus` et sa limite de
processeur.

### 1. Les limites déclarées

`PidsLimit` vaut 16, et la limite mémoire reste en place, à 64 Mio au plus.

### 2. La limite appliquée

Dans le conteneur, `pids.max` vaut 16. Un `ulimit` de shell n'y change rien.

### 3. Une rafale est refusée

Le contrôle lance 24 `sleep` de deux secondes dans le conteneur. Ils tiennent
sous 32 et pas sous 16. Le compteur `max` de `pids.events` doit augmenter. Un
code de sortie non nul ne suffit pas.

### 4. Le service survit

Après une rafale lancée par ce contrôle, `worker` tourne encore, son `StartedAt`
n'a pas changé, et un fichier écrit avant la rafale se relit.

### Ce qui est interdit

Ne lancez aucune boucle de création de processus sans fin, et ne posez pas de
limite sur toute la machine. Le contrôle fait lui-même la rafale.
