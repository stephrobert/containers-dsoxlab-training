# securite-socket-lecture-seule

**Public :** apprenants.

Retirer la capacité d'atteindre le socket du démon, au lieu de la restreindre :
la lecture seule porte sur le fichier du socket, pas sur les requêtes qui y
transitent.

## Ce que vous allez pratiquer

Constater d'abord qu'un `POST` d'arrêt réussit à travers un socket monté en
`:ro`, puis retirer ce montage du conteneur applicatif, par aucun chemin
détourné.

## Limites de sécurité

Seuls les conteneurs et le répertoire de travail portant l'étiquette de ce lab
sont modifiés. Le témoin que vous arrêterez n'existe que pour la démonstration
et est retiré au nettoyage, comme les deux images épinglées, mais seulement si
ce lab les a tirées.

Le socket du démon n'est jamais modifié : le lab retire un montage, il ne touche
ni à la configuration du démon ni aux droits du fichier.

## Validation

Les deux contrôles inspectent l'état effectif sur `docker.lab` ; ni l'historique
des commandes ni le contenu d'un fichier n'accorde de point. Aucun des deux ne
compare des noms de fichiers : l'un résout les sources de montage sur l'hôte,
l'autre relève l'inode de chaque socket visible dans le conteneur. Les messages
d'assertion sont bilingues.
