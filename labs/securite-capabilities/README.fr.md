# Les capabilities Linux

Linux découpe les pouvoirs de root en capabilities. Le sous-ensemble par défaut
de Docker est plus réduit que celui de root sur l'hôte, mais peut encore dépasser
les besoins d'une application. `cap_drop` retire des pouvoirs ; `cap_add` rétablit
ceux explicitement nécessaires. Il faut recréer le conteneur : modifier Compose
ne change pas un processus existant.

Sur un projet jetable neutre `demo-clock`, comparez `HostConfig.CapDrop` et
`CapAdd` de `docker inspect` avec `CapEff` dans `/proc/1/status`.
Le masque est hexadécimal : le bit 0 représente CHOWN, le bit 10
NET_BIND_SERVICE. Une option déclarée et un pouvoir observé par le noyau sont
deux preuves différentes.

Un service HTTP sur un port haut n'a généralement besoin d'aucune capability.
Une écoute réussie sur un port bas ne prouve pas NET_BIND_SERVICE :
`ip_unprivileged_port_start` peut rendre ces ports non privilégiés.

Voir [le challenge](challenge/README.fr.md). Le moteur doit déjà être disponible.
Setup et cleanup préservent les images préexistantes et la configuration du démon.
