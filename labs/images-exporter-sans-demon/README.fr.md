# Exporter une image sans le démon, et garder ce qui doit survivre

La leçon copie une image vers une archive sans passer par le démon. Ce cours
ajoute cinq gestes : lire un index sans rien télécharger, ouvrir une image
posée dans un dossier, peser une copie de toutes les plateformes, ranger
plusieurs images ensemble, et reconnaître une archive abîmée.

Vous travaillez dans `~/essai-export`, sur l'image Alpine, avec le `skopeo` de
Debian installé sur la machine. Le challenge porte sur une autre image et a son
propre lanceur : n'y touchez pas pendant le cours.

Page associée : [Exporter une image sans démon avec Skopeo](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/exporter-sans-demon-avec-skopeo/).

## 🔧 Avant de commencer

Lancez le lab :

```bash
dsoxlab run images-exporter-sans-demon
```

Vous êtes connecté à `docker.lab`, où le moteur tourne. `SOURCE` désigne
l'image dans son registre. **Gardez le même terminal jusqu'au nettoyage** : les
variables n'existent que dans lui.

```bash
mkdir -p ~/essai-export && cd ~/essai-export
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
SOURCE=docker://docker.io/library/alpine@${IMAGE#*@}
skopeo --version
```

```text
skopeo version 1.18.0
```

Les sorties de ce cours viennent d'un Docker 29.9.2 sur Debian 13, le 25
novembre 2026. Les adresses et les identifiants seront différents chez vous.

## 🔭 Exercice 1 : lire un index sans rien télécharger

Demandez le document brut, puis comptez ce qu'il annonce :

```bash
skopeo inspect --raw "$SOURCE" > index.json
python3 -c "
import json
m = json.load(open('index.json'))['manifests']
print(len(m), 'entrees')
print(sorted({x['platform']['architecture'] for x in m}))"
echo "sha256:$(sha256sum index.json | cut -d' ' -f1)" | grep -c "${IMAGE#*@}"
```

```text
16 entrees
['386', 'amd64', 'arm', 'arm64', 'ppc64le', 'riscv64', 's390x', 'unknown']
1
```

Quelques kilo-octets suffisent pour connaître les plateformes. Les entrées
`unknown` ne sont pas des images : ce sont les attestations de construction.
L'empreinte du document est exactement le digest demandé, ce que vous pouvez
vérifier vous-même.

## 📂 Exercice 2 : une image posée dans un dossier

Copiez l'image dans un dossier, et comparez le nom de chaque fichier à son
empreinte :

```bash
skopeo copy -q "$SOURCE" dir:ouvert
ls ouvert | cut -c1-16
for f in ouvert/*; do n=$(basename "$f"); [ "${#n}" = 64 ] && { [ "$(sha256sum "$f" | cut -c1-64)" = "$n" ] && echo conforme; }; done
```

```text
7b229517ed222597
b92841763c5c2140
manifest.json
version
conforme
conforme
```

Le transport `dir:` montre ce qu'une image contient vraiment : un manifeste,
une configuration et des couches, chacune nommée par son empreinte. C'est ce
qui permet de vérifier une image sans la lancer.

## ⚖️ Exercice 3 : une copie de toutes les plateformes

Copiez l'image pour cette machine, puis pour toutes :

```bash
skopeo copy -q "$SOURCE" oci:une
skopeo copy -q --all "$SOURCE" oci:toutes
du -sm une toutes
```

```text
4	une
30	toutes
```

Sans option, `skopeo` choisit la plateforme de la machine. `--all` prend
l'index entier, et son digest est conservé. Le poids suit : choisissez selon
les machines de destination.

## 🗄️ Exercice 4 : plusieurs images ensemble

Rangez deux fois la même image sous deux noms dans un même dossier :

```bash
skopeo copy -q "$SOURCE" oci:lot:matin
skopeo copy -q "$SOURCE" oci:lot:soir
du -sm lot
skopeo inspect oci:lot 2>&1 | grep -o 'more than one image in oci'
skopeo inspect oci:lot:soir --format '{{.Os}}'
```

```text
4	lot
more than one image in oci
linux
```

Le dossier pèse une seule image : les couches communes n'y sont écrites qu'une
fois. Quand il en contient plusieurs, il faut dire laquelle, sinon `skopeo`
refuse de choisir.

## 🩹 Exercice 5 : une archive abîmée

Changez un octet dans une couche, puis coupez une archive, et essayez de vous
en servir :

```bash
skopeo copy -q "$SOURCE" oci-archive:saine.tar:essai-export:1
mkdir a && tar xf saine.tar -C a
printf x | dd of="$(find a/blobs -type f -size +1M)" bs=1 seek=100000 conv=notrunc 2> /dev/null
tar cf abimee.tar -C a .
head -c 2000000 saine.tar > coupee.tar
skopeo copy -q oci-archive:abimee.tar dir:verif 2>&1 | grep -o 'Digest did not match'
docker load -q -i abimee.tar
docker rmi -f essai-export:1 > /dev/null
docker load -q -i coupee.tar 2>&1 | grep -o 'unexpected EOF'
```

```text
Digest did not match
Loaded image: essai-export:1
Error response from daemon: No such image: essai-export:1
unexpected EOF
```

`skopeo` relit chaque couche et refuse l'octet changé. `docker load` a accepté
cette archive abîmée sur cette machine, et n'a refusé que celle qui est coupée.
Vérifiez donc une archive reçue avec `skopeo copy ... dir:`, ou avec une
empreinte transmise à part, avant de la charger.

## 🧹 Nettoyage

```bash
cd ~
rm -rf ~/essai-export
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
dsoxlab reset images-exporter-sans-demon
dsoxlab check images-exporter-sans-demon
```

```text
╭─ Résultat : images-exporter-sans-demon ─╮
│  0 / 100 pts                            │
│  ░░░░░░░░░░░░░░░░░░░░  0/5 tests        │
╰─────────────────────────────────────────╯
```

0 sur 5 : c'est le résultat attendu. Le challenge est prêt.

## 🎯 Le challenge

À vous, seul cette fois : trois archives à produire, et un démon qui ne doit
rien voir.

```bash
dsoxlab run images-exporter-sans-demon
dsoxlab challenge images-exporter-sans-demon
```
