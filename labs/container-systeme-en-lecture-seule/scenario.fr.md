# Un worker qui ne doit pas réécrire son système

Le worker actualise `/run/heartbeat` chaque seconde. Toute sa racine est
modifiable alors qu'il a seulement besoin d'un espace runtime.

Dans `/opt/dsoxlab-container-systeme-en-lecture-seule`, rendez la racine
en lecture seule sans arrêter ce heartbeat. Donnez à `/run` un tmpfs modifiable
de 4 Mio avec noexec et nosuid. Conservez le projet
`dsoxlab-container-systeme-en-lecture-seule` et son label.

Ne modifiez pas les montages hôtes, le démon ni les chemins hôtes. Le contrôle
effectue seulement de petites écritures jetables dans ce conteneur.
