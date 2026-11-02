# Épreuve : remettre trois conteneurs en service

Trois conteneurs d'une même chaîne sont en panne, et **les trois pannes sont
indépendantes**.

## Ce qui est constaté

C'est tout ce qui est constaté, et aucun des trois constats ne dit la cause.

1. `collecteur` est **sorti**, et personne n'a lu son code de sortie.
2. `expediteur` **redémarre sans fin**.
3. `scribe` met **dix secondes** à s'arrêter, et son rapport est **coupé**.

## Les cinq contrôles

Ils sont de poids égal, et chacun porte sur un fait vérifiable.

### 1. Le collecteur tourne, avec l'image fournie

Rien ne le relançait, donc rien ne masquait la cause : son code de sortie et ses
journaux la disent. L'image est vérifiée en plus de l'état : reconstruire une
image à soi règlerait le symptôme et perdrait la leçon.

### 2. L'expéditeur ne redémarre plus, et garde sa politique

**La politique n'est pas la panne** : elle est ce qui rendait la panne visible.
La retirer masque le symptôme sans rien régler, et l'énoncé demande de la
conserver.

La stabilité se mesure **dans le temps** : le contrôle lit le compteur de
redémarrages deux fois, à douze secondes d'intervalle. Un compteur lu une seule
fois ne dit rien, puisqu'il vaut zéro sur un conteneur qui vient d'être recréé.

### 3. Le rapport complet est copié sur l'hôte

**C'est l'exigence critique : elle n'est compensée par aucun total.** Le rapport
vit dans le conteneur, et un conteneur ne survit pas à sa suppression. Un rapport
tronqué copié reste un rapport tronqué : c'est la donnée qui est perdue, pas le
fichier.

Ce rapport porte une **référence propre à ce passage**, écrite dedans au
démarrage. Un scribe détruit puis recréé en écrit une autre : son rapport aura
l'air complet et ne sera pas le bon.

### 4. Aucun conteneur du lab ne traîne à l'arrêt

Un conteneur arrêté garde son nom, sa configuration et son espace disque. Ce
sont eux qui remplissent un disque sans que personne sache d'où ils viennent.

### 5. Le scribe s'arrête proprement, et son rapport est entier

**Trois faits, une seule cause, donc un seul contrôle.** `docker stop` envoie
`SIGTERM`, attend dix secondes, puis `SIGKILL`. Un programme qui reçoit son
signal se termine aussitôt, écrit sa ligne de fin et sort en 0. Un programme qui
ne le reçoit pas consomme tout le délai, sort en 137, et son écriture est
tronquée.

**Ce contrôle est joué en dernier parce qu'il arrête le scribe** : un arrêt ne se
mesure qu'en arrêtant, et aucune lecture après coup ne le remplace.

## Ce qui est fourni

L'image `lab-trois-pannes:1.0` porte les trois rôles. Rien à construire. Elle lit
la variable `ROLE`, et chaque rôle a ses propres exigences.

## Le barème

Cinq contrôles de poids égal, seuil à **75 sur 100**, et **seul l'état final
compte**.

Quatre indices, du plus vague au plus explicite, et **ils coûtent des points** :

```bash
dsoxlab hint
```
