# Lire une image OCI à la main

La leçon ouvre l'image Alpine 3.24.2 avec skopeo et jq : elle résout l'index,
copie l'image dans un layout local, suit la chaîne jusqu'à la couche, puis
altère la configuration pour voir l'image refusée. Ce cours vous fait voir ce
qu'elle ne montre pas. D'abord, pourquoi filtrer un index sur la seule
architecture peut rendre trois manifestes. Ensuite, ce que contient vraiment
une attestation. Puis vous lancerez le programme d'une image sans aucun
moteur. Vous verrez enfin ce que vérifie umoci avant même l'empreinte, ce que
devient un manifeste copié sous deux noms, et ce que `skopeo inspect` rend sur
un layout local.

Vous travaillez sur l'image `hello-world`, dans des dossiers nommés
`/srv/essai-*`. Le challenge porte sur une autre image et un autre layout :
vous le ferez seul, à la fin.

Page associée : [Lire une image OCI et vérifier son digest](https://www.stephane-robert.info/docs/conteneurisation/lire-image-oci/).

## Avant de commencer

Lancez le lab :

```bash
dsoxlab run image-lire-a-la-main
```

Vous êtes maintenant connecté à `oci.lab`, une Debian 13 sans aucun moteur de
conteneurs. Vous êtes l'utilisateur `ansible`, et `sudo` vous donne les droits
de root. Le setup a installé les trois outils de la leçon :

```bash
skopeo --version
umoci --version
jq --version
```

```text
skopeo version 1.18.0
umoci version 0.4.7+ds-4+b10
jq-1.7
```

Les sorties de ce cours ont été relevées sur cette machine le 26 novembre
2026, avec ces versions (le paquet Debian de jq est la 1.7.1, mais l'outil
s'annonce `jq-1.7`). **Gardez le même terminal jusqu'au nettoyage** : les
variables des exercices n'existent que dans lui.

Toutes les commandes partent de l'index de `hello-world`, désigné par son
digest pour que vos sorties soient celles de ce cours :

```bash
HW=docker://docker.io/library/hello-world
HW_INDEX=sha256:1e4c05b897a751332ce85c7e9449da2d93514ea2dea6dbb0e2753c9e949b2bfa
```

## Exercice 1 : une architecture, trois manifestes

La leçon cherche le manifeste `amd64` en filtrant l'index sur
`platform.architecture`. Sur Alpine, cela suffit. Sur `hello-world`, regardez
ce que rend le même filtre :

```bash
skopeo inspect --raw "$HW@$HW_INDEX" > /tmp/essai-hw.raw
sha256sum /tmp/essai-hw.raw
jq -r '.manifests[] | select(.platform.architecture=="amd64") | "\(.platform.os)  \(.platform["os.version"] // "-")  \(.digest)"' /tmp/essai-hw.raw
```

```text
1e4c05b897a751332ce85c7e9449da2d93514ea2dea6dbb0e2753c9e949b2bfa  /tmp/essai-hw.raw
linux  -  sha256:d1a8d0a4eeb63aff09f5f34d4d80505e0ba81905f36158cc3970d8e07179e59e
windows  10.0.26100.33828  sha256:1adee175b582d2873cb2a3df57f5d0f34ec6625a2e795631663f337fa13c7907
windows  10.0.20348.5873  sha256:f8a7a304519b0fc3d5d8a47bd5b417eecea3f97e8b487e2132a7bfb3e00fc467
```

Le `sha256sum` confirme que vous avez bien reçu l'index demandé. Le filtre,
lui, rend trois manifestes : un pour Linux et deux pour Windows, qui tournent
aussi sur des processeurs `amd64`. Une plateforme, c'est un système **et** une
architecture. Les images Windows ajoutent même une version du système
(`os.version`). Pour le manifeste Linux seul, filtrez sur les deux champs :

```bash
jq -r '.manifests[] | select(.platform.os=="linux" and .platform.architecture=="amd64") | .digest' /tmp/essai-hw.raw
```

```text
sha256:d1a8d0a4eeb63aff09f5f34d4d80505e0ba81905f36158cc3970d8e07179e59e
```

Un script qui prendrait la première ligne du premier filtre tomberait juste
ici, par chance d'ordre. Rien ne garantit cet ordre dans un autre index.

## Exercice 2 : ouvrir une attestation

La leçon explique qu'une entrée `unknown/unknown` est une attestation, sans
l'ouvrir. Cherchez celle qui se rattache au manifeste Linux, puis copiez-la
dans un layout comme une image ordinaire :

```bash
LIN=$(jq -r '.manifests[] | select(.platform.os=="linux" and .platform.architecture=="amd64") | .digest' /tmp/essai-hw.raw)
ATT=$(jq -r --arg d "$LIN" '.manifests[] | select(.annotations["vnd.docker.reference.digest"]==$d) | .digest' /tmp/essai-hw.raw)
echo "$ATT"
sudo skopeo copy -q "docker://docker.io/library/hello-world@$ATT" oci:/srv/essai-attestation:attestation
sudo ls -l /srv/essai-attestation/blobs/sha256
```

```text
sha256:8e752a1cddeafc02597e756f4a0ec96e29f63ac4bc4af87682daf3f1de843bb7
total 16
-rw-r--r-- 1 root root  167 Nov 26 06:16 4cc5f49f1578d3d9c4b5f32f6ef7a37d7fadccd4a20f3e29e3bb0ee6cd159f52
-rw-r--r-- 1 root root  566 Nov 26 06:16 8e752a1cddeafc02597e756f4a0ec96e29f63ac4bc4af87682daf3f1de843bb7
-rw-r--r-- 1 root root 4742 Nov 26 06:16 d5e71e642bf52fab99f7dc2746472b824e89b393f60846d6594e7e71aa11c006
```

Trois blobs, comme une image : un manifeste, une configuration et une
« couche ». Mais cette couche n'est pas une archive de fichiers. C'est un
document JSON. Ouvrez-le :

```bash
cd /srv/essai-attestation/blobs/sha256
M=$(jq -r '.manifests[0].digest' ../../index.json | cut -d: -f2)
P=$(jq -r '.layers[0].digest' "$M" | cut -d: -f2)
jq '{predicateType, builder: .predicate.builder.id, buildType: .predicate.buildType}' "$P"
cd /
```

```text
{
  "predicateType": "https://slsa.dev/provenance/v0.2",
  "builder": "https://github.com/docker-library",
  "buildType": "https://mobyproject.org/buildkit@v1"
}
```

C'est une **provenance** : elle dit qui a construit l'image (l'équipe
docker-library) et avec quoi (BuildKit). L'attestation d'Alpine, dans la
leçon, portait aussi un SBOM. Celle de `hello-world` n'en a pas : ce qu'une
attestation contient dépend de celui qui publie l'image.

## Exercice 3 : lancer le programme d'une image sans moteur

Une image n'est qu'un ensemble de fichiers et une fiche de lancement. Copiez
l'image Linux dans un layout, puis listez sa couche :

```bash
sudo skopeo copy -q --override-arch amd64 "$HW@$HW_INDEX" oci:/srv/essai-hw:latest
M=$(jq -r '.manifests[0].digest' /srv/essai-hw/index.json | cut -d: -f2)
L=$(jq -r '.layers[0].digest' /srv/essai-hw/blobs/sha256/$M | cut -d: -f2)
C=$(jq -r '.config.digest' /srv/essai-hw/blobs/sha256/$M | cut -d: -f2)
tar -tzvf /srv/essai-hw/blobs/sha256/$L
```

```text
-rwxr-xr-x 0/0           10072 2026-03-23 21:33 hello
```

La couche contient un seul fichier, `hello`, de 10 072 octets. Sortez-le de
l'archive sans rien dépaqueter d'autre, puis lisez la commande que la
configuration demande de lancer :

```bash
tar -xzOf /srv/essai-hw/blobs/sha256/$L hello > /tmp/essai-hello
chmod +x /tmp/essai-hello
/tmp/essai-hello | head -2
jq -c '.config.Cmd' /srv/essai-hw/blobs/sha256/$C
```

```text

Hello from Docker!
["/hello"]
```

Le programme tourne sur l'hôte, sans moteur. `tar -xzOf` écrit le fichier
demandé sur la sortie standard au lieu de le créer sur le disque. La
configuration dit de lancer `/hello` : c'est exactement ce que vous venez de
faire, mais sans isolation. Le processus voit tout l'hôte. Ce qui manque pour
en faire un conteneur, ce sont les namespaces et les cgroups du module
précédent.

## Exercice 4 : la taille est vérifiée avant l'empreinte

Le manifeste donne, pour chaque blob, son digest **et sa taille**. Comparez la
taille annoncée à celle du fichier, puis ajoutez un octet à la couche, dans
une copie du layout :

```bash
jq '.layers[0].size' /srv/essai-hw/blobs/sha256/$M
stat -c %s /srv/essai-hw/blobs/sha256/$L
sudo cp -a /srv/essai-hw /srv/essai-hw-plus
printf x | sudo tee -a /srv/essai-hw-plus/blobs/sha256/$L > /dev/null
stat -c %s /srv/essai-hw-plus/blobs/sha256/$L
sudo umoci unpack --image /srv/essai-hw-plus:latest /tmp/essai-bundle
```

```text
2415
2415
2416
   ⨯ create runtime bundle: unpack rootfs: discard trailing archive bits: expected 2415 bytes (extra bytes in stream): verified reader size mismatch
```

umoci refuse sur la **taille** (`size mismatch`), avant même de comparer les
empreintes. C'est pour cela que la leçon remplace `/bin/sh` par `/bin/xx`, de
même longueur : pour que seule l'empreinte trahisse la modification.

Faites la même chose sans changer la taille : inversez un bit au milieu de la
couche, dans une autre copie.

```bash
sudo cp -a /srv/essai-hw /srv/essai-hw-octet
sudo python3 -c 'import sys; p=sys.argv[1]; b=bytearray(open(p,"rb").read()); b[1000]^=1; open(p,"wb").write(b)' /srv/essai-hw-octet/blobs/sha256/$L
stat -c %s /srv/essai-hw-octet/blobs/sha256/$L
sudo umoci unpack --image /srv/essai-hw-octet:latest /tmp/essai-bundle
```

```text
2415
   ⨯ create runtime bundle: unpack rootfs: discard trailing archive bits: gzip: invalid checksum
```

La taille est bonne, mais le refus vient cette fois de **gzip** : une archive
compressée porte sa propre somme de contrôle, et un bit inversé la casse. Une
couche altérée peut donc être refusée par trois contrôles : la taille, le
format de l'archive, puis l'empreinte. Seul le dernier garantit que le contenu
est celui qu'on a demandé. Les deux autres ne protègent que d'un accident.

## Exercice 5 : deux noms, un seul manifeste

Copiez la même image deux fois dans un même layout, sous deux tags :

```bash
sudo skopeo copy -q --override-arch amd64 "$HW@$HW_INDEX" oci:/srv/essai-deux:latest
sudo skopeo copy -q --override-arch amd64 "$HW@$HW_INDEX" oci:/srv/essai-deux:stable
jq -r '.manifests[] | "\(.annotations["org.opencontainers.image.ref.name"])  \(.digest)"' /srv/essai-deux/index.json
ls /srv/essai-deux/blobs/sha256 | wc -l
```

```text
latest  sha256:d1a8d0a4eeb63aff09f5f34d4d80505e0ba81905f36158cc3970d8e07179e59e
stable  sha256:d1a8d0a4eeb63aff09f5f34d4d80505e0ba81905f36158cc3970d8e07179e59e
3
```

`index.json` a deux entrées, mais elles désignent le même manifeste, et le
magasin ne compte que trois blobs. Un blob est rangé sous le nom de son
contenu : le même contenu ne peut pas être stocké deux fois. Un tag n'est
qu'une étiquette posée sur un digest.

## Exercice 6 : ce que rend skopeo inspect sur un layout

La leçon montre que, sur le registre, le champ `Digest` de `skopeo inspect`
reste celui de l'index. Comparez avec le même champ lu sur votre layout :

```bash
skopeo inspect --format '{{.Digest}}' "$HW@$HW_INDEX"
skopeo inspect --format '{{.Digest}}' oci:/srv/essai-hw:latest
```

```text
sha256:1e4c05b897a751332ce85c7e9449da2d93514ea2dea6dbb0e2753c9e949b2bfa
sha256:d1a8d0a4eeb63aff09f5f34d4d80505e0ba81905f36158cc3970d8e07179e59e
```

Sur le registre, c'est le digest de l'index. Sur le layout, c'est celui du
manifeste Linux, puisque la copie n'a gardé que lui. Le même champ ne désigne
donc pas le même objet selon l'endroit où vous le lisez. Avant de noter un
digest, sachez ce qu'il désigne.

## Nettoyage

Retirez tout ce que ce cours a créé, puis vérifiez qu'il ne reste rien :

```bash
sudo rm -rf /srv/essai-attestation /srv/essai-hw /srv/essai-hw-plus /srv/essai-hw-octet /srv/essai-deux /tmp/essai-bundle
rm -f /tmp/essai-hw.raw /tmp/essai-hello
ls -d /srv/essai-* /tmp/essai-* 2>/dev/null || echo "aucun fichier d'essai"
```

```text
aucun fichier d'essai
```

Plus rien de ce cours. Quittez ensuite la machine et remettez le lab à zéro.
`dsoxlab reset` rejoue le nettoyage puis la préparation du lab : vous
retrouvez exactement l'état de départ du challenge. Il vous demande de
confirmer : répondez `y`.

```bash
exit
dsoxlab reset image-lire-a-la-main
dsoxlab check image-lire-a-la-main
```

```text
╭─ Résultat : image-lire-a-la-main ─╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests  │
╰───────────────────────────────────╯
```

0 sur 4 : c'est le résultat attendu. Le challenge vous attend, intact.

## Le challenge

À vous, seul cette fois : copier busybox par digest dans un layout local, noter
le digest de son manifeste `amd64`, et trouver le seul blob altéré d'un layout
reçu d'ailleurs.

```bash
dsoxlab run image-lire-a-la-main
dsoxlab challenge image-lire-a-la-main
```
