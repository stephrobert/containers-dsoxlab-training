# L'image qui se construit, et dont personne ne peut se servir

## La situation

Le build est vert. L'image est dans le magasin local, le pipeline dit que tout
est passé, et l'équipe qui la reçoit la lance lundi matin.

À dix heures, trois choses ont mal tourné, et aucune ne se voyait la veille.
Un conteneur a démarré, mais rien ne répond sur le port qu'il publie. Un autre
refuse de dire pourquoi il s'est arrêté. Un troisième a été tué au bout de dix
secondes au lieu de s'arrêter, et le compteur qu'il gardait en mémoire est
parti avec lui.

Personne n'a testé l'image **de l'extérieur**, comme le font les gens qui la
font tourner. Les tests unitaires du code passaient, et ils ne pouvaient rien
attraper de tout cela : les défauts sont dans l'image, pas dans le programme.

## Ce qu'un utilisateur de l'image peut attendre

| Attente | Ce que cela veut dire pour le guichet |
| --- | --- |
| Elle démarre | elle répond à `GET /ouvert` par un 200 sur le port `8099`, atteint par un port publié |
| Elle fait son travail | `POST /ticket` répond 201 et délivre le numéro suivant, `GET /tickets` rend le nombre de tickets délivrés |
| Elle se configure | sans `GUICHET_SITE` elle s'arrête aussitôt, avec un code non nul et un message qui nomme la variable ; avec elle, `/ouvert` mentionne le site |
| Elle n'exige aucun privilège | le processus n'est pas root, et le service tourne encore quand le conteneur est lancé avec un système de fichiers en lecture seule, son dossier de données `/var/lib/guichet` étant le seul endroit inscriptible |
| Elle s'arrête quand on le demande | `docker stop` la termine bien avant le délai de grâce de dix secondes, avec le code 0 ou 143, et le compteur est toujours là quand on remonte le même dossier de données |

## Énoncé

Travaillez sur `docker.lab`, dans `/opt/dsoxlab-images-tester-le-contrat`. Le
contexte du service est dans `guichet/`. Les images `guichet:1.0` (correcte) et
`guichet:0.9` (cassée) sont déjà construites.

Écrivez **`tester-contrat.sh`** dans ce répertoire. `bash tester-contrat.sh
<image>` rend 0 quand l'image respecte le contrat ci-dessous, et un code non nul
sinon.

L'énoncé est aussi déposé dans `/opt/dsoxlab-images-tester-le-contrat/MISSION.md`.

### 1. Il accepte l'image correcte, et ne laisse rien derrière lui

`bash tester-contrat.sh guichet:1.0` rend 0. Quand il rend la main, aucun
conteneur et aucun volume qu'il a créé ne subsiste, quel que soit le résultat.

### 2. Il refuse une image qui ne démarre pas, ou qu'on ne peut pas joindre

Le service répond à `GET /ouvert` par un 200 sur le port `8099`, **par un port
publié**. Une image qui tourne sans être joignable ainsi, ou qui s'arrête au
démarrage, est refusée. N'attendez pas un temps fixe : bornez l'attente.

### 3. Il refuse une configuration mal vérifiée

Sans `GUICHET_SITE`, le service doit s'arrêter vite, avec un code **non nul** et
un message qui nomme la variable. Une image qui s'arrête avec le code 0, ou qui
démarre quand même, est refusée.

### 4. Il refuse une image qui en demande trop

Le processus ne doit pas tourner en root, et le service doit tourner encore
quand le conteneur est lancé en lecture seule, avec `/var/lib/guichet` pour seul
endroit inscriptible.

### 5. Il refuse une image qui s'arrête mal

`docker stop` doit terminer le conteneur bien avant dix secondes, avec le code 0
ou 143, et le compteur doit survivre : après avoir monté le même dossier de
données dans un nouveau conteneur, `GET /tickets` rend le nombre de tickets
délivrés avant l'arrêt.

### 6. Il refuse ce qu'il ne peut pas juger

Sans argument, ou avec le nom d'une image qui n'existe pas, il rend un code non
nul.

### Ce que vous ne devez pas toucher

Ne modifiez pas la configuration du démon, et ne supprimez pas `guichet:1.0` :
les contrôles construisent leurs propres images à partir d'elle.

### Ce qui n'est pas noté

La formulation de vos messages, l'ordre de vos contrôles et le langage du
script, du moment que `bash tester-contrat.sh <image>` le lance.

Deux images sont nommées dans cet énoncé. Les contrôles jouent votre script
contre d'autres, que vous n'avez pas vues : n'écrivez pas un script qui les
reconnaît par leur nom.
