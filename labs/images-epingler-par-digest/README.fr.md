# Garder le socle approuvé quand son tag change

La leçon écrit un digest dans un `FROM` et prouve qu'il tient. Ce cours cherche
par où un build peut quand même changer : un argument qui remplace l'épingle,
une seconde dépendance oubliée, la trace de ce qui a servi, un digest recopié
au mauvais endroit, et une épingle dont l'objet a été supprimé.

Vous travaillez sur un registre `essai-registre`, en HTTP sur la boucle locale,
et sur des images `essai-*`. Le challenge porte sur `dsoxlab-pin-registry` et
sur `/opt/lab-image-pin` : n'y touchez pas pendant le cours.

Page associée : [Épingler un socle, et livrer hors ligne](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/epingler-et-livrer-hors-ligne/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run images-epingler-par-digest
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. `socle` construit une
version du socle, la publie sous le tag `stable` et rend son digest. `A` est
l'ancien, `B` le nouveau : `stable` désigne `B`. **Gardez le même terminal
jusqu'au nettoyage** : les variables n'existent que dans lui.

```bash
mkdir -p ~/essai-epingle && cd ~/essai-epingle
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
R=127.0.0.1:15099
docker run -d --name essai-registre -p $R:5000 -e REGISTRY_STORAGE_DELETE_ENABLED=true registry:3.1.2@sha256:d4032d4cc323c1731c707931ecada07a53076eac38e3b61ae57533f170f2c6c3 > /dev/null
sleep 3
socle() { printf 'FROM %s\nRUN echo %s > /version\n' "$IMAGE" "$1" | docker build -q -t $R/essai-socle:stable - > /dev/null; docker push -q $R/essai-socle:stable > /dev/null; docker buildx imagetools inspect $R/essai-socle:stable --format '{{.Manifest.Digest}}'; }
A=$(socle ancien); B=$(socle nouveau)
[ "$A" != "$B" ] && echo 'deux digests'
```

```text
29.9.2
deux digests
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🪪 Exercice 1 : une épingle remplacée à la construction

Mettez la référence épinglée dans un argument, puis construisez avec et sans le
remplacer :

```bash
printf 'ARG SOCLE=%s/essai-socle@%s\nFROM $SOCLE\nCMD ["cat", "/version"]\n' $R $A > Dockerfile
docker build -q -t essai-a . > /dev/null && docker run --rm essai-a
docker build -q --build-arg SOCLE=$R/essai-socle:stable -t essai-b . > /dev/null && docker run --rm essai-b
grep -c "$A" Dockerfile
```

```text
ancien
nouveau
1
```

Le fichier n'a pas changé et porte toujours l'épingle, mais la seconde image
est sur l'autre socle. Un `ARG` est une valeur par défaut. Si la chaîne de
construction n'a pas à choisir le socle, écrivez la référence directement dans
le `FROM`.

## 🧩 Exercice 2 : la dépendance oubliée

Épinglez le `FROM`, copiez un fichier depuis une autre image par son tag, puis
ramenez `stable` sur l'ancien :

```bash
printf 'FROM %s\nCOPY --from=%s/essai-socle:stable /version /v\nCMD ["cat", "/v"]\n' "$IMAGE" $R > Dockerfile
docker build -q --pull --no-cache -t essai-c . > /dev/null && docker run --rm essai-c
docker buildx imagetools create -t $R/essai-socle:stable $R/essai-socle@$A > /dev/null 2>&1
docker build -q --pull --no-cache -t essai-c . > /dev/null && docker run --rm essai-c
grep -nE '^(FROM|COPY --from)' Dockerfile | grep -v '@sha256:' | cut -d' ' -f1
```

```text
nouveau
ancien
2:COPY
```

Le `FROM` est épinglé et le produit a changé quand même. Toute image nommée
dans le fichier est une dépendance : chaque `FROM` et chaque `COPY --from` qui
vise une image. La dernière commande liste ceux qui n'ont pas de digest.

## 🧾 Exercice 3 : ce qui a vraiment servi

Demandez à la construction la liste de ce qu'elle a consommé :

```bash
docker build -q --pull --no-cache --metadata-file trace.json -t essai-c . > /dev/null
cat > lire.py <<'EOF'
import json
for m in json.load(open("trace.json"))["buildx.build.provenance"]["materials"]:
    print(m["uri"].split("?")[0], m["digest"]["sha256"][:12])
EOF
python3 lire.py | sed "s/$(echo ${A#sha256:} | cut -c1-12)/(digest de A)/"
```

```text
pkg:docker/127.0.0.1:15099/essai-socle@stable (digest de A)
pkg:docker/alpine@3.24.3 be2656061b53
```

Même pour une référence par tag, la trace donne le digest résolu ce jour-là.
C'est ce qui permet, après coup, de savoir quel socle a servi et de l'épingler.
Conservez ce fichier avec l'image livrée.

## 📍 Exercice 4 : un digest recopié au mauvais endroit

Utilisez le bon digest avec un autre dépôt, puis l'identifiant d'une image
jamais publiée, puis un digest tronqué :

```bash
essai() { printf 'FROM %s\n' "$1" | docker build --pull - 2>&1 | grep '^ERROR: failed to build' | grep -oE 'not found|insufficient_scope|invalid checksum digest length' | tail -1; }
essai $R/essai-autre@$A
essai essai-a@$(docker image inspect essai-a --format '{{.Id}}')
essai $R/essai-socle@${A%????}
essai $R/essai-socle@$A || echo 'aucune erreur'
```

```text
not found
insufficient_scope
invalid checksum digest length
```

Un digest se lit dans un dépôt : le même, demandé ailleurs, est introuvable.
L'identifiant d'une image locale ressemble à un digest, mais aucun registre ne
le connaît : ici, Docker est allé le demander à Docker Hub. Seul le couple
dépôt et digest désigne quelque chose.

## 🕳️ Exercice 5 : une épingle sur un objet supprimé

Gardez l'ancien socle en local, supprimez-le du registre, puis cherchez qui le
voit encore :

```bash
docker pull -q $R/essai-socle@$A > /dev/null
curl -s -o /dev/null -w '%{http_code}\n' -X DELETE http://$R/v2/essai-socle/manifests/$A
printf 'FROM %s/essai-socle@%s\nCMD ["cat", "/version"]\n' $R $A > Dockerfile
docker build -q --pull -t essai-d . > /dev/null && docker run --rm essai-d
skopeo inspect --tls-verify=false docker://$R/essai-socle@$A 2>&1 | grep -oE 'manifest unknown' | head -1
docker tag $R/essai-socle@$A $R/essai-socle:approuve
docker push -q $R/essai-socle:approuve > /dev/null
skopeo inspect --tls-verify=false docker://$R/essai-socle@$A > /dev/null && echo 'de nouveau lisible, meme digest'
```

```text
202
ancien
manifest unknown
de nouveau lisible, meme digest
```

Sur cette machine, le build réussit même avec `--pull` : le contenu désigné par
le digest est déjà là. Ailleurs, il échouerait, car le registre ne l'a plus.
L'épingle garantit le contenu, pas sa conservation. Gardez un tag sur les
versions approuvées, pour que le ménage du registre ne les emporte pas.

## 🧹 Nettoyage

```bash
cd ~
docker rm -fv essai-registre > /dev/null
docker images --format '{{.Repository}}:{{.Tag}}@{{.Digest}}' | grep 'essai-' | sed 's/:<none>//; s/\(:[a-z]*\)@.*/\1/' | sort -u | xargs -r docker rmi -f > /dev/null
rm -rf ~/essai-epingle
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
docker images --format '{{.Repository}}' | grep -c 'essai-\|15547'
```

```text
0
0
```

Quittez ensuite la machine et remettez le lab à zéro. `dsoxlab reset` rejoue le
nettoyage puis la préparation du lab. Il vous demande de confirmer : répondez
`y`.

```bash
exit
dsoxlab reset images-epingler-par-digest
dsoxlab check images-epingler-par-digest
```

```text
╭─ Résultat : images-epingler-par-digest ─╮
│  0 / 100 pts                            │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests        │
╰─────────────────────────────────────────╯
```

0 sur 3 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : un socle approuvé à garder, quoi que devienne son
tag.

```bash
dsoxlab run images-epingler-par-digest
dsoxlab challenge images-epingler-par-digest
```
