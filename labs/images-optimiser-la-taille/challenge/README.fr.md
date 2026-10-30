# Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service. Le contexte est dans
`/opt/lab-taille/appli` :

```text
Dockerfile      il MARCHE, et l'image pèse sept fois son contenu
attendus.txt    les trois artefacts que l'application utilise
src/main.sh     le code, qui imprime un jeton et l'empreinte de fabrication
```

**Commencez par construire et peser.** Puis entrez dans l'image : le cache de
fabrication n'y est pas, les artefacts y sont. Pesez enfin **chaque couche**.

## 1. L'image doit fonctionner et porter ses artefacts

`appli:legere` doit imprimer son jeton **et** une empreinte de fabrication, et
porter les trois artefacts de `attendus.txt`.

Ce contrôle existe pour une raison précise : le moyen le plus rapide d'alléger
une image est de ne plus rien y mettre. L'empreinte prouve en outre que la
fabrication a bien eu lieu **dans cette image**.

## 2. Aucune couche ne doit porter le cache

C'est le cœur du lab, et la mesure qui le rend visible.

Le conteneur ne montre rien : une couche ultérieure supprime le cache, donc il
est introuvable dans l'image assemblée. Il est pourtant là, **dans une couche**,
et il est téléchargé avec elle.

Mesuré sur cette machine : **44 Mo** de couche pour un nettoyage joué une
instruction trop tard, **6,3 Mo** quand il est joué dans la même.

## 3. La taille totale doit rester proche du nécessaire

Deux mesures plutôt qu'une, et elles ne disent pas la même chose.

Une couche peut rester sous son plafond pendant que plusieurs, ensemble, pèsent
le double du nécessaire : un cache écrit en deux fois, ou un second
téléchargement, se répartit sans jamais faire une grosse couche.

Le seuil est **calculé** : le socle est pesé, les artefacts aussi. Rien n'est
écrit dans le dépôt.

## 4. L'image doit toujours dériver du socle

Aplatir l'image donne la bonne taille, et c'est refusé.

Mesuré ici : 14,6 Mo en **une** couche, exactement le poids de la bonne
écriture. Les deux contrôles de pesée seraient verts.

Et elle ne partage plus aucune couche avec son socle. Les couches communes sont
ce qui fait qu'un dépôt ne stocke le socle qu'une fois, et qu'un poste qui l'a
déjà ne télécharge que la différence. Une image aplatie est stockée et
transférée **en entier**, pour chaque variante.

**La taille se gagne dans les instructions, pas après coup.**

## Ce qui n'est pas noté

La commande que vous avez tapée. Le nettoyage peut s'écrire de plusieurs façons
tant qu'il a lieu dans l'instruction qui a créé ce qu'il retire.
