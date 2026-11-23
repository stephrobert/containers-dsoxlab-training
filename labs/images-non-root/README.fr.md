# Faire tourner une image sans root

La leçon montre que `USER` change l'identité sans donner aucun droit, comment
donner un répertoire au bon uid, ce que fait `COPY --chown`, et pourquoi
déclarer un uid numérique. Ce cours vous fait mesurer ce que coûte un
`RUN chown` mal placé, voir la différence entre un volume nommé et un
répertoire de l'hôte monté dans le conteneur, écrire dans ce répertoire sous
votre propre uid, et entrer en root dans un conteneur non-root pour le
diagnostiquer.

Vous travaillez dans `~/essai-droits`, avec des images `essai-droits:*` et
l'uid d'essai `30100`. Le challenge porte sur une autre application et un
autre uid : vous le ferez seul, à la fin.

Page associée : [Utilisateur et permissions dans une image](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/utilisateur-et-permissions/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run images-non-root
```

Vous êtes maintenant connecté à `docker.lab`, une Debian 13 où le moteur
Docker tourne. Créez le répertoire d'essai et rangez le socle du cours dans
une variable. **Gardez le même terminal jusqu'au nettoyage** : la variable
n'existe que dans lui.

```bash
mkdir -p ~/essai-droits && cd ~/essai-droits
ALPINE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
```

Les sorties de ce cours ont été relevées sur cette machine le 23 novembre 2026,
avec Docker Engine 29.9.2.

## 📏 Exercice 1 : ce que coûte un `RUN chown`

La leçon dit que `COPY --chown` économise une couche. Mesurez ce que cette
couche pèse. Créez un fichier de 10 Mo, puis construisez deux images qui le
donnent à l'uid `30100` : l'une par un `RUN chown` après le `COPY`, l'autre
par `COPY --chown`.

```bash
head -c 10000000 /dev/urandom > donnees.bin
printf 'FROM %s\nCOPY donnees.bin /srv/donnees.bin\nRUN chown 30100:30100 /srv/donnees.bin\n' "$ALPINE" > Dockerfile.run
printf 'FROM %s\nCOPY --chown=30100:30100 donnees.bin /srv/donnees.bin\n' "$ALPINE" > Dockerfile.copy
docker build -q -t essai-droits:run -f Dockerfile.run .
docker build -q -t essai-droits:copy -f Dockerfile.copy .
docker history --format '{{.Size}}\t{{.CreatedBy}}' essai-droits:run | head -2 | cut -c1-60
docker history --format '{{.Size}}\t{{.CreatedBy}}' essai-droits:copy | head -1 | cut -c1-60
docker image ls --format '{{.Repository}}:{{.Tag}} {{.Size}}' | grep '^essai-droits'
```

```text
sha256:5966fe639b6fdeafad9523ccb581fc65497c6b6b150aecdba01fc95473b3f228
sha256:8ffd04df14162c70dd34f88abb267d33fc024fdaf43726e9f90b2086786b317c
10MB	RUN /bin/sh -c chown 30100:30100 /srv/donnee…
10MB	COPY donnees.bin /srv/donnees.bin # buildkit
10MB	COPY --chown=30100:30100 donnees.bin /srv/do…
essai-droits:copy 33MB
essai-droits:run 53MB
```

Le `RUN chown` ne modifie pas le fichier sur place : il en écrit une nouvelle
copie dans une nouvelle couche. Le même fichier de 10 Mo est donc stocké deux
fois, et l'image pèse 20 Mo de plus. `COPY --chown` pose le propriétaire au
moment de la copie, en une seule couche.

## 📂 Exercice 2 : volume nommé ou répertoire de l'hôte

Construisez une image non-root qui écrit dans `/srv/carnet`, un répertoire
donné à l'uid `30100`. Lancez-la d'abord sur un volume nommé, puis sur un
répertoire de votre dossier personnel monté à la même place :

```bash
cat > Dockerfile.nonroot <<EOF
FROM $ALPINE
RUN mkdir -p /srv/carnet && chown 30100:30100 /srv/carnet
USER 30100:30100
CMD ["sh", "-c", "date > /srv/carnet/derniere && echo ecrit"]
EOF
docker build -q -t essai-droits:nonroot -f Dockerfile.nonroot .
docker volume create essai-carnet >/dev/null
docker run --rm -v essai-carnet:/srv/carnet essai-droits:nonroot
docker run --rm -v essai-carnet:/srv/carnet --entrypoint stat essai-droits:nonroot -c '%u:%g %n' /srv/carnet
mkdir -p ~/essai-droits/hote
docker run --rm -v ~/essai-droits/hote:/srv/carnet essai-droits:nonroot; echo "code=$?"
stat -c '%u:%g %n' ~/essai-droits/hote
```

```text
sha256:9f90851f878c1fd9ff25cc9d1fd952dc08b7e78003fdcbe62e262c1bfd20e666
ecrit
30100:30100 /srv/carnet
sh: can't create /srv/carnet/derniere: Permission denied
code=1
1001:1001 /home/ansible/essai-droits/hote
```

Le volume nommé, vide à sa création, a reçu le propriétaire du répertoire de
l'image (`30100:30100`) : Docker recopie ce répertoire dans le volume la
première fois. L'écriture passe. Le répertoire de l'hôte, lui, est monté
**tel quel** : il appartient à votre compte (uid 1001 ici), et l'uid `30100` du
conteneur n'a pas le droit d'y écrire. Le `chown` du Dockerfile ne s'applique
pas à un répertoire de l'hôte.

## ✍️ Exercice 3 : écrire dans le répertoire de l'hôte sous votre uid

Pour écrire dans un répertoire de l'hôte, le processus doit avoir un uid qui y
a le droit. Lancez la même image sous votre propre uid, avec `--user` :

```bash
docker run --rm --user "$(id -u):$(id -g)" -v ~/essai-droits/hote:/srv/carnet essai-droits:nonroot; echo "code=$?"
ls -ln ~/essai-droits/hote | tail -1 | awk '{print $3":"$4, $9}'
```

```text
ecrit
code=0
1001:1001 derniere
```

L'écriture passe, et le fichier créé vous appartient sur l'hôte : vous pourrez
le lire et le supprimer sans `sudo`. C'est la réponse habituelle pour un outil
qui écrit dans votre répertoire de travail. Ce n'est pas celle d'une image de
service : elle doit écrire sans qu'on lui passe d'option, comme dans
l'exercice 2.

## 🩺 Exercice 4 : entrer en root dans un conteneur non-root

Un conteneur non-root ne peut rien modifier hors de ce qui lui appartient,
même pour un diagnostic. Lancez l'image en arrière-plan, puis comparez une
commande ordinaire et une commande lancée avec `docker exec -u 0` :

```bash
docker run -d --name essai-veille essai-droits:nonroot sleep 300 >/dev/null
docker exec essai-veille id
docker exec essai-veille sh -c 'touch /etc/essai'; echo "code=$?"
docker exec -u 0 essai-veille id
docker exec -u 0 essai-veille sh -c 'touch /etc/essai && echo ecrit-en-root'
```

```text
uid=30100 gid=30100 groups=30100
touch: /etc/essai: Permission denied
code=1
uid=0(root) gid=0(root) groups=0(root),1(bin),2(daemon),3(sys),4(adm),6(disk),10(wheel),11(floppy),20(dialout),26(tape),27(video)
ecrit-en-root
```

`docker exec` reprend l'uid de l'image, `30100`, et ne peut pas écrire dans
`/etc`. Avec `-u 0`, la même commande tourne en root, dans le même conteneur.
C'est utile pour diagnostiquer, et c'est aussi pour cela qu'un accès au moteur
Docker vaut un accès root : le `USER` de l'image ne protège pas d'un
administrateur du moteur.

## 🧹 Nettoyage

Supprimez le conteneur, les images, le volume et le répertoire d'essai. Les
deux dernières commandes comptent les images et les volumes `essai-*` qui
restent :

```bash
cd ~
docker rm -f essai-veille >/dev/null
docker rmi essai-droits:run essai-droits:copy essai-droits:nonroot | grep -c Untagged
docker volume rm essai-carnet
rm -rf ~/essai-droits
docker images --format '{{.Repository}}' | grep -c '^essai-'; docker volume ls -q | grep -c '^essai-'
```

```text
3
essai-carnet
0
0
```

Plus rien de ce cours. Quittez ensuite la machine et remettez le lab à zéro.
`dsoxlab reset` rejoue le nettoyage puis la préparation du lab : vous
retrouvez exactement l'état de départ du challenge. Il vous demande de
confirmer : répondez `y`.

```bash
exit
dsoxlab reset images-non-root
dsoxlab check images-non-root
```

```text
╭─── Résultat : images-non-root ────╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests  │
╰───────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge vous attend, intact.

## 🎯 Le challenge

À vous, seul cette fois : faire tourner une application sous un uid non nul
déclaré par l'image, sans qu'elle perde le droit d'écrire son journal, et
sans ouvrir son répertoire à tout le monde.

```bash
dsoxlab run images-non-root
dsoxlab challenge images-non-root
```
