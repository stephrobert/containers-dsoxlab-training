# Exporter une image sans le démon

Ce lab livre une image épinglée du registre sous forme de trois archives, sur un
hôte dont le démon ne doit jamais la tirer. Un lanceur fourni apporte Skopeo
1.22.3, la version de l'éditeur et non celle de la distribution.

Cinq contrôles prouvent la livraison, et chacun échoue avant tout travail.
L'archive OCI porte l'image attendue, vérifiée par ses couches ; le store local
du démon ne garde aucune trace de l'image source, ce qu'un `docker pull` suivi
d'un `docker save` ne saurait obtenir ; l'archive se charge en une image nommée,
puisque Skopeo accepte une destination sans nom et que seul `docker load` en
montre la conséquence ; l'archive arm64 porte bien arm64 sur un hôte amd64 ; et
l'archive docker-archive est au format historique, avec son entrée
`repositories` et son `<id>/layer.tar`.

Ce qui n'est pas noté, et pourquoi : les droits des archives. Skopeo écrit en
0644 de lui-même, donc l'exiger récompenserait l'état initial.

Deux faits mesurés façonnent le lab. Sur un store containerd, l'identifiant
local est le digest du manifeste, et il change donc légitimement à la conversion
de format : le lab montre ce qu'il devient au lieu d'exiger qu'il survive. Et
les couches d'une image dans le démon sont les diff_ids décompressés, jamais
comparables aux digests compressés du registre, quel que soit l'outil qui les
lit.

Le nettoyage ne retire que ce que le setup a posé, d'après des marqueurs qu'il
écrit lui-même.
