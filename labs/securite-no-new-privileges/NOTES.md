# no_new_privs

`USER` choisit une identité initiale, pas un plafond permanent de privilèges.
Exécuter un binaire setuid appartenant à root peut changer l'UID effectif.
Le drapeau Linux `no_new_privs` interdit à `execve` d'accorder de nouveaux
privilèges, notamment par setuid ou capabilities de fichier. Il est hérité et
ne peut pas être désactivé.

Sur un projet Compose jetable neutre `demo-reader`, ajoutez l'option de sécurité
`no-new-privileges:true`, puis recréez le service. Comparez `NoNewPrivs` dans
`/proc/1/status` avant et après. Retirer les capabilities et choisir un UID
non-root sont des contrôles complémentaires, pas des substituts à ce drapeau.

L'exercice compile une sonde C d'identité inoffensive depuis Alpine épinglée.
La compilation nécessite l'accès aux paquets Alpine. Aucun compilateur ni
binaire setuid hôte n'est modifié. La configuration Docker reste intacte.

Voir [le challenge](challenge/README.fr.md).
