# Énoncé

Travaillez sur `docker.lab`, dans `/opt/dsoxlab-images-tester-le-contrat`. Le
contexte du service est dans `guichet/`. Les images `guichet:1.0` (correcte) et
`guichet:0.9` (cassée) sont déjà construites.

Écrivez **`tester-contrat.sh`** dans ce répertoire. `bash tester-contrat.sh
<image>` rend 0 quand l'image respecte le contrat ci-dessous, et un code non nul
sinon.

## 1. Il accepte l'image correcte, et ne laisse rien derrière lui

`bash tester-contrat.sh guichet:1.0` rend 0. Quand il rend la main, aucun
conteneur et aucun volume qu'il a créé ne subsiste, quel que soit le résultat.

## 2. Il refuse une image qui ne démarre pas, ou qu'on ne peut pas joindre

Le service répond à `GET /ouvert` par un 200 sur le port `8099`, **par un port
publié**. Une image qui tourne sans être joignable ainsi, ou qui s'arrête au
démarrage, est refusée. N'attendez pas un temps fixe : bornez l'attente.

## 3. Il refuse une configuration mal vérifiée

Sans `GUICHET_SITE`, le service doit s'arrêter vite, avec un code **non nul** et
un message qui nomme la variable. Une image qui s'arrête avec le code 0, ou qui
démarre quand même, est refusée.

## 4. Il refuse une image qui en demande trop

Le processus ne doit pas tourner en root, et le service doit tourner encore
quand le conteneur est lancé en lecture seule, avec `/var/lib/guichet` pour seul
endroit inscriptible.

## 5. Il refuse une image qui s'arrête mal

`docker stop` doit terminer le conteneur bien avant dix secondes, avec le code 0
ou 143, et le compteur doit survivre : après avoir monté le même dossier de
données dans un nouveau conteneur, `GET /tickets` rend le nombre de tickets
délivrés avant l'arrêt.

## 6. Il refuse ce qu'il ne peut pas juger

Sans argument, ou avec le nom d'une image qui n'existe pas, il rend un code non
nul.

## Ce qui n'est pas noté

La formulation de vos messages, l'ordre de vos contrôles et le langage du
script, du moment que `bash tester-contrat.sh <image>` le lance.

Deux images sont nommées dans cet énoncé. Les contrôles jouent votre script
contre d'autres, que vous n'avez pas vues : n'écrivez pas un script qui les
reconnaît par leur nom.
