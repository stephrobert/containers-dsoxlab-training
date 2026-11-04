# Cahier des charges

Travaillez sur `docker.lab`, dans `/opt/dsoxlab-securite-seccomp`.

1. Gardez un `worker` actif, projet `dsoxlab-securite-seccomp`,
   label `dsoxlab.lab=securite-seccomp`.
2. Attachez un profil seccomp JSON explicite, pas `unconfined`.
3. PID 1 doit annoncer le mode de filtrage 2.
4. `/usr/local/bin/syscall-probe`, déjà fourni, doit observer
   `getpgid(sentinel)=EPERM getpgid(0)=allowed getpid=allowed`.
   L'argument sentinelle vaut 2147483647 ; ne bloquez pas les appels runtime ordinaires.
5. **Dérivez `seccomp-defaut.json`, le profil par défaut du moteur fourni avec
   le lab**, plutôt que d'écrire un profil neuf. Tout ce que ce profil refuse
   déjà doit rester refusé : le contrôle joue `unshare -U` dans le conteneur, et
   il doit échouer. N'ajoutez aucune capacité.

Un profil dont le `defaultAction` vaut `SCMP_ACT_ALLOW` permet tout sauf les
lignes qu'il refuse : c'est une liste noire, et ce n'est jamais ce qu'un service
doit porter.

Gardez la sonde fournie et les plafonds de ressources. Ne modifiez pas le démon.
