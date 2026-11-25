# Diagnostiquer ENOSPC, pas nettoyer tout l'hôte

ENOSPC peut signaler l'épuisement des blocs ou des inodes. `df -h` indique la
capacité, `df -i` les inodes et `du` attribue l'usage des fichiers visibles.
Un fichier supprimé encore ouvert peut garder son espace jusqu'à sa fermeture.

Sur un projet jetable neutre `demo-spool`, identifiez le montage contenant le
chemin en échec avant toute suppression. Retirer un fichier explicitement
jetable de ce montage n'est pas purger tout le moteur Docker.
Vérifiez les données conservées et prouvez la récupération par une écriture finie.

L'exercice simule l'épuisement de capacité dans un tmpfs local au conteneur,
strictement plafonné à 16 Mio, dans un cgroup de 64 Mio sans swap.
Il reproduit ENOSPC sans danger, pas la latence disque, la comptabilité des
couches Docker ni l'épuisement d'une partition hôte. Le dd initial est limité à
16 blocs. Ni montage loopback ni modification du démon hôte.

Le moteur et Compose doivent déjà être disponibles, avec au moins 128 Mio de
mémoire hôte disponible. Voir [le challenge](challenge/README.fr.md).
