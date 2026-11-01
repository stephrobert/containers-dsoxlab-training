# Un processus non-root peut encore acquérir des privilèges

Le worker démarre sous UID 1000, mais son petit exécutable `identity` appartient
à root en mode 4755. Il affiche seulement les UID réel et effectif : ni shell
ni modification de fichiers. Sans barrière de privilèges, son exécution obtient
EUID 0.

Dans `/opt/dsoxlab-securite-no-new-privileges`, gardez ce binaire intact mais
empêchez l'élévation dans le service actif. Conservez le projet
`dsoxlab-securite-no-new-privileges` et son label. Le drapeau du noyau et une
véritable exécution doivent concorder.

Ne modifiez aucun binaire hôte, aucune politique setuid ni le démon.
