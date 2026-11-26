# Un OOM qui reste dans son conteneur

## La situation

Le service `worker` tourne avec 96 Mio de mémoire. Son contrat de déploiement
lui en accorde 32, sans swap. Vous devez le ramener dans ce budget, et vérifier
qu'une allocation trop grande y est tuée sans emporter le service.

## Mission

Sur `docker.lab`, le projet Compose est dans
`/opt/dsoxlab-container-memoire-et-oom`, sous le nom
`dsoxlab-container-memoire-et-oom`. Gardez un seul `worker` en marche, avec son
label `dsoxlab.lab=container-memoire-et-oom` et ses limites de tâches et de
processeur.

### 1. Les limites déclarées

`Memory` et `MemorySwap` valent tous deux 33554432, soit 32 Mio. La machine n'a
pas de swap : c'est le contrat qui demande de l'interdire, pas un débordement
que vous pourriez observer ici.

### 2. Les limites appliquées

Dans le conteneur, `memory.max` vaut 33554432 et `memory.swap.max` vaut 0.

### 3. Une allocation trop grande est tuée

Le contrôle lance dans le conteneur une allocation limitée, qui passe sous
96 Mio et pas sous 32. Elle doit être tuée, et le compteur `oom_kill` de
`memory.events` doit augmenter. Un code de sortie non nul ne suffit pas.

### 4. Le service survit

Après un OOM provoqué par ce contrôle, `worker` tourne encore, son `StartedAt`
n'a pas changé, et un fichier écrit avant l'incident se relit.

### Ce qui est interdit

Ne stressez pas la machine, ne changez pas son swap et ne lancez pas
d'allocation sans limite. Si la machine manque de mémoire libre, le contrôle
s'arrête et vous le dit : ce n'est pas votre travail qui est en cause.
