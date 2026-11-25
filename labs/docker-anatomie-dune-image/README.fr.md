# L'anatomie d'une image : couches, partage, configuration

La leçon présente l'image, le conteneur et le registre. Ce cours ouvre des
images que vous construisez : un fichier effacé qui pèse encore, deux images
identiques qui n'en sont pas, un ordre qui coûte cher, une étiquette de
configuration, et la couche que chaque conteneur ajoute.

Vous travaillez dans `~/essai-couches`, sur des images `essai-*`. Le challenge
porte sur `greffe:1.0` et `greffe:2.0` : ne les examinez pas pendant le cours.

Page associée : [Images, conteneurs et registres : l'anatomie](https://www.stephane-robert.info/docs/conteneurs/moteurs-conteneurs/docker/anatomie/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run docker-anatomie-dune-image
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. `bati` construit une
image depuis un Dockerfile lu sur l'entrée ; `couches` liste ses couches.
**Gardez le même terminal jusqu'au nettoyage** : les variables n'existent que
dans lui.

```bash
mkdir -p ~/essai-couches && cd ~/essai-couches
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
bati() { docker build -q --build-arg IMAGE="$IMAGE" -t "essai-$1" -f - . > /dev/null; }
couches() { docker image inspect "$1" --format '{{range .RootFS.Layers}}{{println .}}{{end}}' | grep sha256; }
couches "$IMAGE" | wc -l
```

```text
29.9.2
1
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 👻 Exercice 1 : un fichier effacé qui pèse encore

Créez un fichier puis effacez-le, d'abord en deux instructions, ensuite en une
seule :

```bash
printf 'ARG IMAGE\nFROM $IMAGE\nRUN head -c 5000000 /dev/urandom > /gros\nRUN rm /gros\n' | bati deux
printf 'ARG IMAGE\nFROM $IMAGE\nRUN head -c 5000000 /dev/urandom > /gros && rm /gros\n' | bati une
docker save essai-deux -o deux.tar
docker save essai-une -o une.tar
echo "ecart : $(( ($(stat -c %s deux.tar) - $(stat -c %s une.tar)) / 1000000 )) Mo"
docker run --rm essai-deux ls /gros
mkdir x && tar xf deux.tar -C x && for b in x/blobs/sha256/*; do tar tf "$b" 2> /dev/null | grep -E '^gros$|^\.wh\.gros$'; done | sort
```

```text
ecart : 5 Mo
ls: /gros: No such file or directory
.wh.gros
gros
```

Le fichier a disparu du conteneur et l'image pèse toujours son poids : la
seconde couche ne fait que le cacher, par une marque `.wh.`. Un secret effacé
de cette façon se retrouve donc dans l'archive.

## 👯 Exercice 2 : deux images identiques qui n'en sont pas

Construisez une image, changez seulement la date d'un fichier et recommencez,
puis changez seulement une étiquette :

```bash
echo contenu > f; touch -d '2026-01-01' f
printf 'ARG IMAGE\nFROM $IMAGE\nCOPY f /f\n' | bati un
touch -d '2026-02-01' f
printf 'ARG IMAGE\nFROM $IMAGE\nCOPY f /f\n' | bati date
printf 'ARG IMAGE\nFROM $IMAGE\nCOPY f /f\nLABEL note=a\n' | bati note
compare() { [ "$(couches essai-$1)" = "$(couches essai-$2)" ] && C=memes || C=autres; echo "$1 et $2 : $C couches"; [ "$(docker image inspect essai-$1 -f '{{json .Config}}')" = "$(docker image inspect essai-$2 -f '{{json .Config}}')" ] && echo '   meme configuration' || echo '   autre configuration'; }
compare un date
compare un note
docker run --rm essai-date stat -c '%y' /f | cut -c1-10
```

```text
un et date : memes couches
   meme configuration
un et note : memes couches
   autre configuration
2026-01-01
```

La date d'un fichier ne compte pas pour le cache de construction : la couche
est reprise, et le fichier garde sa première date. Une étiquette, elle, change
la configuration sans changer une seule couche. Comparez les couches pour
parler du contenu, et la configuration à part.

## 🔀 Exercice 3 : un ordre qui coûte cher

Écrivez deux fois deux images, avec la même instruction lourde avant ou après
le fichier qui change :

```bash
echo 1 > v1; echo 2 > v2
for v in 1 2; do
  printf "ARG IMAGE\nFROM \$IMAGE\nRUN seq 500000 > /outils\nCOPY v$v /v\n" | bati avant$v
  printf "ARG IMAGE\nFROM \$IMAGE\nCOPY v$v /v\nRUN seq 500000 > /outils\n" | bati apres$v
done
partage() { comm -12 <(couches essai-$1 | sort) <(couches essai-$2 | sort) | wc -l; }
echo "lourde avant : $(partage avant1 avant2) couches partagees sur $(couches essai-avant1 | wc -l)"
echo "lourde apres : $(partage apres1 apres2) couches partagees sur $(couches essai-apres1 | wc -l)"
```

```text
lourde avant : 2 couches partagees sur 3
lourde apres : 1 couches partagees sur 3
```

Le contenu produit est le même, mais l'instruction placée après le fichier qui
change est rejouée, et donne une couche neuve. Mettez ce qui change le moins en
premier : la partie lourde n'est alors stockée qu'une fois.

## 🏷️ Exercice 4 : ce qui n'est dans aucune couche

Donnez à une image une variable et une commande, et cherchez-les dans les
fichiers puis dans la configuration :

```bash
printf 'ARG IMAGE\nFROM $IMAGE\nENV EQUIPE=paie\nCMD ["echo", "salut"]\n' | bati conf
[ "$(couches essai-conf)" = "$(couches "$IMAGE")" ] && echo 'memes couches que la base'
docker run --rm essai-conf sh -c 'grep -rl EQUIPE=paie /etc /root /home 2> /dev/null | wc -l'
docker image inspect essai-conf --format '{{json .Config.Cmd}} {{json .Config.Env}}' | sed 's/PATH=[^"]*/PATH=.../'
docker run --rm essai-conf env | grep EQUIPE
docker history essai-conf --format '{{.CreatedBy}}' | head -2 | cut -c1-40
```

```text
memes couches que la base
0
["echo","salut"] ["PATH=...","EQUIPE=paie"]
EQUIPE=paie
CMD ["echo" "salut"]
ENV EQUIPE=paie
```

L'image a exactement les couches de sa base : sa commande et sa variable sont
dans la configuration, à part. Le moteur les applique au lancement. Une image
est donc une pile de fichiers **et** une fiche.

## 📝 Exercice 5 : la couche de chaque conteneur

Lancez deux conteneurs de la même image, écrivez dans l'un, et voyez ce que
chacun a ajouté :

```bash
for c in un deux; do docker run -d --name essai-$c "$IMAGE" sleep 600 > /dev/null; done
docker exec essai-un sh -c 'echo x > /nouveau; echo y >> /etc/motd; rm /etc/issue'
docker diff essai-un | sort
docker diff essai-deux | wc -l
docker exec essai-deux ls /etc/issue
docker commit essai-un essai-fige > /dev/null
echo "couches : $(couches "$IMAGE" | wc -l) puis $(couches essai-fige | wc -l)"
docker rm -f essai-un essai-deux > /dev/null
```

```text
A /nouveau
C /etc
C /etc/motd
D /etc/issue
0
/etc/issue
couches : 1 puis 2
```

Chaque conteneur a sa propre couche d'écriture ; celles de l'image sont
partagées et ne changent jamais. `A` est un ajout, `C` un changement, `D` un
effacement. `docker commit` fige cette couche, sans dire comment elle a été
faite : préférez un Dockerfile.

## 🧹 Nettoyage

```bash
cd ~
docker images -q --filter 'reference=essai-*:latest' | sort -u | xargs docker rmi -f > /dev/null
rm -rf ~/essai-couches
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Quittez ensuite la machine et remettez le lab à zéro. `dsoxlab reset` rejoue le
nettoyage puis la préparation du lab. Il vous demande de confirmer : répondez
`y`.

```bash
exit
dsoxlab reset docker-anatomie-dune-image
dsoxlab check docker-anatomie-dune-image
```

```text
╭─ Résultat : docker-anatomie-dune-image ─╮
│  0 / 100 pts                            │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests        │
╰─────────────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : deux images à disséquer, et une valeur qui n'est dans
aucun fichier.

```bash
dsoxlab run docker-anatomie-dune-image
dsoxlab challenge docker-anatomie-dune-image
```
