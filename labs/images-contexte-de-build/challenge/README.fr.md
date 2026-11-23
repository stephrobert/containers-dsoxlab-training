# Le moteur dit qu'il ne trouve pas un fichier qui est là

## La situation

Une application ne se construit plus. Le message est net :

```text
ERROR: ... "/commun/version.txt": not found
```

On va voir. Le fichier est là, lisible, à sa place. On le lit, on le touche, on
refait la construction : même message. On cherche alors une faute de frappe, un
problème de droits, un montage qui aurait disparu. On perd une heure sur un
fichier qui n'a jamais manqué.

Il manque pour le moteur, et c'est tout autre chose.

## L'objectif

Le dépôt est dans `/opt/lab-contexte/depot` :

```text
appli/        l'application, son Dockerfile et son code
commun/       un fichier PARTAGÉ entre plusieurs applications
secrets/      un secret de production
archives/     20 Mo dont personne n'a besoin
```

Construisez, lisez le message, et allez vérifier que le fichier existe. Puis
demandez-vous ce que le moteur, lui, pouvait voir.

Faites tourner `appli:contexte`, qui doit imprimer son jeton **et** la version
partagée.

**Trois contraintes, et chacune est notée :**

1. `commun/version.txt` reste la **source unique**. Le recopier dans `appli/`
   réglerait la construction et créerait la divergence que ce rangement existe
   pour éviter.
2. ni le secret ni les archives n'entrent dans l'image.
3. la construction se rejoue par un script `construire.sh` à la racine du dépôt,
   en **chemins relatifs**.

L'énoncé est aussi déposé dans `/opt/MISSION.md`.

## Ce que le message ne dit plus

Mesuré sur cette machine, le même Dockerfile sous les deux constructeurs :

| Constructeur | Message |
| --- | --- |
| buildkit, le défaut aujourd'hui | `"/commun/version.txt": not found` |
| le classique, `DOCKER_BUILDKIT=0` | `forbidden path outside the build context` |

Le second **nommait la cause**. Le premier dit « introuvable », parce que le
`..` est normalisé puis écrasé : le moteur ne regarde que dans le contexte, et
rend compte de ce qu'il voit, pas de ce qui est.

C'est pourquoi tant de réponses trouvées en ligne parlent d'un fichier manquant,
et pourquoi ce lab commence par faire lire le message plutôt que par le corriger.

## Ce que ce lab ne note pas, et pourquoi

Le **poids du contexte**. On lit partout qu'un contexte volumineux ralentit la
construction, et c'était vrai. Mesuré ici : avec 20 Mo d'archives dans le dépôt,
`transferring context` annonce **2 octets**, et l'image pèse exactement la taille
du socle. Buildkit n'envoie que ce dont les `COPY` ont besoin.

Noter le temps de transfert mesurerait donc une croyance. Ce qui reste vrai, et
ce que le lab note, c'est qu'élargir le contexte met tout le dépôt à portée d'un
`COPY .`, **secret compris**. Une image se transmet, et ce qui y entre en repart
avec elle.

## Ce qui est noté

L'**état du système**, et il est mesuré par l'effet. Les contrôles rejouent
votre `construire.sh` dans une **copie** du dépôt, une fois tel quel, une fois
après avoir changé la version partagée : l'image reconstruite doit porter la
nouvelle valeur. C'est ce qui distingue un fichier partagé d'une copie figée, et
aucune lecture du Dockerfile n'est nécessaire pour le dire.

Votre image n'est pas perdue au passage : son étiquette est mise de côté le temps
de la mesure, puis rendue.

## Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable, moteur en service. Le dépôt est dans
`/opt/lab-contexte/depot` :

```text
appli/Dockerfile        il ÉCHOUE, sur un fichier qui existe
appli/src/main.sh       le code, qui imprime un jeton et la version partagée
commun/version.txt      le fichier PARTAGÉ, source unique
secrets/jeton-prod.txt  un secret de production
archives/dump.bin       20 Mo dont personne n'a besoin
```

**Commencez par construire et lire le message.** Il dit que
`/commun/version.txt` est introuvable. Allez vérifier : le fichier est là. Ce
n'est donc pas lui qui manque, et c'est tout le lab.

### 1. Rendez la construction rejouable

Un script `construire.sh` à la racine du dépôt, en **chemins relatifs**.

Ce n'est pas une coquetterie : les trois autres contrôles **rejouent ce
script**. Une commande qui ne vit que dans l'historique d'un terminal n'est pas
reproductible, et il n'y aurait alors aucun moyen de vérifier quoi que ce soit.

Un chemin absolu repointerait sur le dépôt d'origine, et construirait autre
chose que ce qu'on lit.

### 2. L'image doit porter le code et la version partagée

`appli:contexte` doit imprimer son jeton **et** la version venue de `commun/`.

Un `COPY` ne sort **jamais** du contexte, et `..` ne l'y aide pas : le chemin est
normalisé, puis écrasé. Le contexte décide de ce qu'un `COPY` peut atteindre, et
il se choisit à la construction.

Le Dockerfile, lui, n'a pas à se trouver dans le contexte : il peut rester là où
il décrit quelque chose.

### 3. Ni le secret ni les archives n'entrent dans l'image

Élargir le contexte met **tout le dépôt** à portée d'un `COPY .`.

Une image se transmet, et ce qui y entre en repart avec elle. Le contrôle cherche
le **contenu** du secret partout dans l'image, et pas seulement son chemin
d'origine.

À noter, parce qu'on lit souvent le contraire : sous le constructeur actuel, un
contexte volumineux n'est **pas** envoyé en entier. Mesuré ici, 20 Mo dans le
dépôt donnent `transferring context: 2B`. Le sujet n'est donc pas le temps de
transfert, c'est ce qui entre dans l'image.

### 4. Le fichier partagé reste la source unique

Le recopier dans `appli/` réglerait la construction en une commande, et c'est
refusé.

`commun/` sert à plusieurs applications. Deux copies d'une même vérité, c'est
une divergence en attente : l'une sera modifiée, l'autre oubliée, et le jour où
cela se verra, les deux images diront des choses différentes.

Le contrôle le mesure par l'effet : il change la version dans une **copie** du
dépôt, rejoue votre script, et l'image reconstruite doit porter la **nouvelle**
valeur. Votre image est mise de côté le temps de la mesure, puis rendue.

### Ce qui n'est pas noté

La commande que vous avez tapée, et le chemin choisi. Le Dockerfile peut être
désigné ou déplacé, l'exclusion peut passer par un fichier dédié ou par des
copies ciblées : c'est l'état qui compte.
