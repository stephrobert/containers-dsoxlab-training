# Notes du défi

Utilisez les valeurs propres à la session dans `state.env` ; les noms de base
sont aléatoires afin que le nettoyage ne touche pas une base préexistante au
nom courant. La notation restaure la sauvegarde indépendamment : copier
directement les lignes dans la base cible ne suffit pas. La cible est
`docker-client.lab`, pas une seconde base sur `docker.lab`. Le fichier transféré
doit avoir la même empreinte SHA-256 que la sauvegarde source.
