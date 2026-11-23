# Maîtriser le contexte de build

La leçon explique que `docker build` ne voit que son contexte, comment
l'élargir avec `-f`, et comment en écarter un fichier sensible. Ce cours vous
fait vérifier ce que le constructeur reçoit vraiment, écrire des exclusions
avec une exception, extraire d'une image un fichier pourtant supprimé, et
construire sans aucun contexte.

Vous travaillez dans des répertoires d'essai de votre dossier personnel, avec
des images `essai-*`. Le challenge porte sur un autre dépôt et un autre
Dockerfile : vous le ferez seul, à la fin.

Page associée : [Écrire un Dockerfile](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/ecrire-dockerfile/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run images-contexte-de-build
```

Vous êtes maintenant connecté à `docker.lab`, une Debian 13 où le moteur
Docker tourne. Les sorties de ce cours ont été relevées sur cette machine le
23 novembre 2026, avec Docker Engine 29.9.2.

## 📦 Exercice 1 : voir ce que le constructeur reçoit

Le contexte, c'est ce que `docker build` envoie au constructeur. Pour le voir,
écrivez un Dockerfile qui copie tout le contexte puis liste ce qu'il a reçu.
L'option `--progress=plain` affiche la sortie des commandes `RUN`.

```bash
mkdir -p ~/essai-contexte/journaux ~/essai-contexte/brouillons && cd ~/essai-contexte
echo rapport > rapport.txt
echo a > journaux/lundi.log
echo b > journaux/garder.log
echo c > brouillons/idee.txt
cat > Dockerfile <<'EOF'
FROM alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
COPY . /contexte
RUN find /contexte -type f | sort
EOF
docker build --no-cache --progress=plain -t essai-contexte:1 . 2>&1 | grep -E '^#[0-9]+ [0-9.]+ /contexte|transferring context'
```

```text
#3 transferring context: 2B done
#5 transferring context: 436B done
#7 0.125 /contexte/Dockerfile
#7 0.125 /contexte/brouillons/idee.txt
#7 0.125 /contexte/journaux/garder.log
#7 0.125 /contexte/journaux/lundi.log
#7 0.125 /contexte/rapport.txt
```

La première ligne `transferring context` concerne le Dockerfile, la seconde le
contexte : quelques centaines d'octets. Les cinq fichiers du répertoire sont
arrivés, Dockerfile compris : un `COPY .` emporte tout ce que le contexte
contient.

## 🚫 Exercice 2 : exclure par motifs, avec une exception

Un `.dockerignore` accepte des motifs. Écartez le répertoire des brouillons et
tous les fichiers `.log`, sauf `journaux/garder.log`, que vous rattrapez avec
un `!`. Puis reconstruisez :

```bash
cat > .dockerignore <<'EOF'
brouillons/
**/*.log
!journaux/garder.log
EOF
docker build --no-cache --progress=plain -t essai-contexte:2 . 2>&1 | grep -E '^#[0-9]+ [0-9.]+ /contexte'
```

```text
#7 0.134 /contexte/.dockerignore
#7 0.134 /contexte/Dockerfile
#7 0.134 /contexte/journaux/garder.log
#7 0.134 /contexte/rapport.txt
```

`brouillons/` et `lundi.log` ne sont plus envoyés. `garder.log` revient grâce
à la ligne `!`, qui doit venir **après** le motif qu'elle corrige : les lignes
se lisent dans l'ordre, et la dernière qui correspond l'emporte. Le
`.dockerignore` lui-même entre dans l'image, parce que rien ne l'exclut.

## 🔍 Exercice 3 : un fichier supprimé reste dans l'image

La leçon dit qu'ajouter un `RUN rm` ne retire pas un fichier de l'image. Vérifiez
le vous-même : copiez une note privée, supprimez-la à l'instruction suivante,
puis cherchez son contenu dans les couches de l'image.

```bash
mkdir -p ~/essai-couche && cd ~/essai-couche
echo MotDePasse-Essai-42 > note-privee.txt
cat > Dockerfile <<'EOF'
FROM alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
COPY note-privee.txt /tmp/
RUN rm /tmp/note-privee.txt
EOF
docker build -q -t essai-couche:1 .
docker run --rm essai-couche:1 ls -A /tmp | wc -l
docker history --format '{{.CreatedBy}}' essai-couche:1 | head -3
```

```text
sha256:29f1eb12fb14943246c233acf5ab71ab73ef926810d823403be1a3f7a38412a5
0
RUN /bin/sh -c rm /tmp/note-privee.txt # bui…
COPY note-privee.txt /tmp/ # buildkit
CMD ["/bin/sh"]
```

Dans un conteneur lancé depuis l'image, `/tmp` est vide : 0 fichier. Mais
`docker history` montre que la couche du `COPY` existe toujours, sous celle du
`RUN rm`. Exportez maintenant l'image avec `docker save`, puis cherchez le mot
de passe dans chacune de ses couches :

```bash
mkdir extrait && docker save essai-couche:1 | tar -x -C extrait
for c in $(find extrait/blobs -type f); do tar -xOf "$c" 2>/dev/null | grep -a -q MotDePasse-Essai-42 && echo "trouvé dans la couche $(basename "$c" | cut -c1-12)"; done
```

```text
trouvé dans la couche 4b0310bcf1a4
```

Le mot de passe est lisible dans une couche de l'image. Quiconque récupère
l'image le retrouve de la même façon. Le `RUN rm` a seulement ajouté une couche
qui masque le fichier. Seule une exclusion du contexte l'aurait gardé dehors.

## 🧱 Exercice 4 : construire sans aucun contexte

`docker build -` lit le Dockerfile sur l'entrée standard, et n'envoie **aucun**
contexte. Construisez deux Dockerfile ainsi : l'un ne fait qu'un `RUN`, l'autre
un `COPY`.

```bash
mkdir -p ~/essai-sans && cd ~/essai-sans
printf 'FROM alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a\nRUN echo construit sans contexte\n' > Dockerfile.run
printf 'FROM alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a\nCOPY rapport.txt /\n' > Dockerfile.copy
docker build -q -t essai-sans:run - < Dockerfile.run
docker build -t essai-sans:copy - < Dockerfile.copy 2>&1 | tail -1
```

```text
sha256:9b3605b0165e869f05b025e042ed49d6dc0ed81550e51616b077818d4a63c4e1
ERROR: failed to build: failed to solve: failed to compute cache key: failed to calculate checksum of ref rkzv83qyclf9yx7nyebxnoute::h2ug2pc3u64fwu6cyb4md7ca9: "/rapport.txt": not found
```

Le premier se construit : un `RUN` n'a besoin d'aucun fichier. Le second
échoue avec `not found`, le même message que dans la leçon, alors qu'il n'y a
pas de faute de frappe : sans contexte, `COPY` n'a rien où chercher. Devant ce
message, demandez-vous toujours d'abord ce que le constructeur a reçu.

## 🧹 Nettoyage

Supprimez les images et les répertoires d'essai. La dernière commande compte
les images `essai-*` qui restent :

```bash
cd ~
docker rmi essai-contexte:1 essai-contexte:2 essai-couche:1 essai-sans:run | grep -c Untagged
rm -rf ~/essai-contexte ~/essai-couche ~/essai-sans
docker images --format '{{.Repository}}' | grep -c '^essai-'
```

```text
4
0
```

Plus aucune image d'essai. Quittez ensuite la machine et remettez le lab à
zéro. `dsoxlab reset` rejoue le nettoyage puis la préparation du lab : vous
retrouvez exactement l'état de départ du challenge. Il vous demande de
confirmer : répondez `y`.

```bash
exit
dsoxlab reset images-contexte-de-build
dsoxlab check images-contexte-de-build
```

```text
╭─ Résultat : images-contexte-de-build ─╮
│  0 / 100 pts                          │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests      │
╰───────────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge vous attend, intact.

## 🎯 Le challenge

À vous, seul cette fois : faire construire une application dont le Dockerfile
réclame un fichier partagé hors de son répertoire, sans laisser entrer dans
l'image un secret qui se trouve à côté.

```bash
dsoxlab run images-contexte-de-build
dsoxlab challenge images-contexte-de-build
```
