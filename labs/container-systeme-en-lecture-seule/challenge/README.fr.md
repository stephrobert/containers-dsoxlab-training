# Un worker qui ne doit pas réécrire son système

## La situation

Sur `docker.lab`, le `worker` du projet `dsoxlab-container-systeme-en-lecture-seule`
écrit l'heure dans `/run/heartbeat` chaque seconde. C'est sa seule écriture, et
pourtant toute sa racine est modifiable. Le projet se trouve dans
`/opt/dsoxlab-container-systeme-en-lecture-seule`.

## Mission

1. La racine est en lecture seule : une vraie écriture dans `/` échoue.
2. `/run` est un tmpfs inscriptible de 4 Mio exactement, avec `noexec` et `nosuid`.
3. Le worker tourne et `/run/heartbeat` continue d'avancer.

Gardez le projet, l'étiquette `dsoxlab.lab=container-systeme-en-lecture-seule`,
la commande fournie, l'image épinglée et les limites de ressources. N'ajoutez
aucun montage de l'hôte et ne modifiez pas le démon. Le contrôle fait quelques
petites écritures dans le conteneur, puis les retire.
