# Cahier des charges

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
