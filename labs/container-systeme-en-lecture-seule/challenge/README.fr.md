# Cahier des charges

Travaillez sur `docker.lab`, dans `/opt/dsoxlab-container-systeme-en-lecture-seule`.

1. Gardez `worker` actif dans le projet `dsoxlab-container-systeme-en-lecture-seule`,
   label `dsoxlab.lab=container-systeme-en-lecture-seule`.
2. Activez la racine en lecture seule ; une vraie écriture dans `/` doit échouer.
3. Fournissez un tmpfs `/run` modifiable de 4 Mio exactement, noexec et nosuid.
4. Gardez la commande fournie actualisant `/run/heartbeat`.

Préservez l'image épinglée et les ressources bornées. Ni montage hôte ni édition
du démon.
