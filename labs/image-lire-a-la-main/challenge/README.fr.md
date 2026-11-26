# Une image à vérifier avant de l'accepter

## La situation

Sur `oci.lab`, une Debian 13 sans moteur de conteneurs, l'équipe veut
n'accepter que des images qu'elle a vérifiées elle-même. Elle vous confie deux
tâches : copier busybox 1.37.0 par digest et noter ce qu'elle contient, puis
examiner un layout reçu d'ailleurs, `/srv/suspect`, dont un fichier a été
modifié.

skopeo, jq et umoci sont installés. Vous êtes `root` par `sudo`.

L'image de référence est l'index de busybox 1.37.0 :

```text
docker.io/library/busybox@sha256:a7dbc319b1438115a207e11930dc4bb3e643dcb3ec0bdd694bb36cd8fad289ec
```

## Ce que vous devez obtenir

1. **`/srv/etal`** est un layout OCI qui porte busybox 1.37.0 pour
   `linux/amd64`, copiée par ce digest, sous le tag **`1.37.0`**.
2. Chaque blob de `/srv/etal` porte l'empreinte de son nom.
3. Le fichier **`/srv/reponses/manifeste-amd64`** contient le digest du
   manifeste `linux/amd64` de cette image.
4. Le fichier **`/srv/reponses/blob-altere`** contient le **nom** du blob de
   `/srv/suspect` qui a été modifié.

Une réponse s'écrit sur une ligne, avec ou sans le préfixe `sha256:`.

## Les repères utiles

`/srv/suspect` porte deux images, `amd64` et `arm64`, donc six blobs. La
modification n'a pas changé la taille du fichier : seule l'empreinte la
trahit. Le blob modifié est tiré au hasard à chaque `dsoxlab reset`.

Le digest d'une plateforme se lit dans l'index servi par le registre, pas dans
le champ `Digest` d'un `skopeo inspect` qui reçoit `--override-arch`.

## Comment vous saurez que c'est bon

Les tests lisent `oci-layout` et `index.json` de `/srv/etal`, recalculent
l'empreinte de chacun de ses blobs, et comparent vos deux réponses au digest
attendu et au blob que le setup a modifié.

```bash
dsoxlab check image-lire-a-la-main
```
