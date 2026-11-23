# Livrer une image sans que le démon la touche

Une machine de livraison doit préparer trois archives d'image pour un site qui
n'a aucun accès au registre. Vous travaillez dans
`/opt/dsoxlab-images-exporter-sans-demon`, et `skopeo` y est déjà installé sous
la forme d'une image épinglée : la commande `skopeo` du répertoire l'appelle,
vous n'avez rien à installer.

L'image à livrer est **`busybox:1.37.0-musl`**, épinglée par le digest de son
index : `sha256:f6a95d611e0a8780fabdb2aec43e31275b2720dfefa3e41b16835bfc42454478`.

## Ce qu'il faut produire

1. **`livraison/socle-oci.tar`**, une archive au format **OCI**, copiée
   **directement depuis le registre**, portant le nom de destination complet
   `livraison.test/socle:1.0`.
2. **`livraison/socle-docker.tar`**, la même image au format **docker-archive**,
   avec le même nom de destination. Les deux formats n'ont ni la même structure
   ni la même taille, et c'est ce que la livraison doit montrer.
3. **`livraison/socle-arm64.tar`**, une archive OCI de la variante **arm64** de
   cette même image, alors que cet hôte est amd64.

## Ce que le démon ne doit jamais faire

**Le démon ne doit pas avoir tiré l'image.** C'est tout le sujet : `skopeo`
parle au registre lui-même, sans passer par lui. Après votre travail,
`docker images` ne doit porter aucune trace de `busybox:1.37.0-musl`.

Un `docker pull` suivi d'un `docker save` produirait une archive, et serait
refusé : cette voie exige justement que le démon tire l'image, ce qu'un hôte
sans démon ne peut pas faire.

## Ce qui doit survivre au transport, et ce qui change

Chargez `livraison/socle-oci.tar` dans le démon pour le vérifier vous-même.
Trois nombres s'appellent « identité », et le transport ne les traite pas
pareil :

- l'**identifiant local** (`.Id`) **change**, et c'est normal : ce moteur stocke
  ses images avec containerd, où cet identifiant est le digest du manifeste, et
  la conversion de format reconstruit le manifeste ;
- le **digest de configuration**, que `skopeo inspect` rend sous `Digest`,
  **survit** ;
- les **couches** (`RootFS.Layers`) **survivent**.

Un transport qui changerait les couches n'aurait pas livré la même image.

## Deux pièges que vous allez rencontrer

**Un tag et un digest ensemble sont refusés.** `nom:tag@sha256:...` ne se nomme
pas ainsi : skopeo répond `references with both a tag and digest are currently
not supported`. Nommez par le digest seul, ou par le tag seul.

**Une destination sans nom donne une image sans nom.** `docker load` affiche
alors `Loaded image ID: sha256:...` au lieu de `Loaded image: ...`, et le site
reçoit une image qu'il doit renommer avant de pouvoir s'en servir.

**Et une archive docker-archive ne se réécrit pas.** Si vous recommencez une
livraison, skopeo refuse : `docker-archive doesn't support modifying existing
images`. Retirez le fichier d'abord. L'`oci-archive`, lui, l'accepte : c'est une
différence de plus entre les deux formats.

Ne changez pas la configuration du démon et ne touchez pas aux autres images de
la machine.

## Cahier des charges

Travaillez sur `docker.lab`, dans `/opt/dsoxlab-images-exporter-sans-demon`.
Le lanceur `skopeo` y est fourni : appelez-le par `./skopeo`, vous n'avez rien
à installer. `A-LIVRER.txt` rappelle l'image et son digest.

1. **`livraison/socle-oci.tar`** est une archive au **format OCI** : elle porte
   un `oci-layout`, un `index.json` et des `blobs/sha256/`. Elle contient bien
   l'image à livrer, vérifiée par son digest de configuration.
2. **Le démon n'a jamais tiré cette image.** `docker image inspect
   busybox:1.37.0-musl` doit échouer. Copiez depuis le registre avec
   `docker://` en transport de source ; un `docker pull` suivi d'un
   `docker save` est refusé, puisqu'il exige du démon ce qu'un hôte sans démon
   ne peut pas faire.
3. **L'archive se charge en une image nommée**, `livraison.test/socle:1.0`, et
   **ses couches sont celles de la source**. L'identifiant local, lui, change :
   c'est normal, et le scénario dit pourquoi.
4. **`livraison/socle-arm64.tar`** porte l'architecture **arm64**, alors que cet
   hôte est amd64, et son manifeste diffère de celui de l'archive principale.
5. **`livraison/socle-docker.tar`** est au format **docker-archive** : elle
   porte un `manifest.json` à plat et **aucun** `oci-layout`.

Ce qui n'est pas noté : les droits des archives. `skopeo` écrit en 0644 de
lui-même, donc l'exiger ne mesurerait rien ; c'est `docker save` qui écrit en
0600, et le contraste appartient à la leçon.

Ne changez pas la configuration du démon et ne touchez pas aux autres images de
la machine.
