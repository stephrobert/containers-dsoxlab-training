# Cahier des charges

Travaillez sur `docker.lab`, dans `/opt/dsoxlab-securite-seccomp`.

1. Gardez un `worker` actif, projet `dsoxlab-securite-seccomp`,
   label `dsoxlab.lab=securite-seccomp`.
2. Attachez un profil seccomp JSON explicite, pas `unconfined`.
3. PID 1 doit annoncer le mode de filtrage 2.
4. `/usr/local/bin/syscall-probe`, déjà fourni, doit observer
   `getpgid(sentinel)=EPERM getpgid(0)=allowed getpid=allowed`.
   L'argument sentinelle vaut 2147483647 ; ne bloquez pas les appels runtime ordinaires.

Gardez la sonde fournie et les plafonds de ressources. Ne modifiez pas le démon.
