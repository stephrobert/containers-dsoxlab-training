# Resserrer le profil du moteur, et non le remplacer

## La situation

Sur `docker.lab`, le `worker` du projet `dsoxlab-securite-seccomp` tourne sans
filtre (`unconfined`). Votre équipe veut lui refuser un seul appel,
`getpgid(2147483647)`, et rien d'autre. Cet identifiant de processus n'existe
pas : sans filtre, l'appel rend ESRCH ; refusé, il rend EPERM.

Le projet se trouve dans `/opt/dsoxlab-securite-seccomp`. Il contient
`seccomp-defaut.json`, une copie épinglée du profil par défaut de Docker
(`moby/profiles`, `seccomp/v0.3.0`) : le moteur embarque le sien dans son
binaire, il n'y a pas de fichier à relever sur l'hôte.

## Mission

1. Attachez à `worker` un profil JSON, pas `unconfined`.
2. PID 1 annonce le mode de filtrage 2.
3. `/usr/local/bin/syscall-probe`, déjà dans l'image, affiche
   `getpgid(sentinel)=EPERM getpgid(0)=allowed getpid=allowed`.
4. **Le profil dérive de `seccomp-defaut.json`.** Tout ce que ce profil refuse
   reste refusé : le contrôle joue `unshare -U` dans le conteneur, qui doit
   échouer.

Le profil par défaut autorise `getpgid` sans condition. Un refus ajouté à côté de
cette autorisation ne mord pas : il faut que les deux cas ne se recouvrent pas.
Un profil dont le `defaultAction` vaut `SCMP_ACT_ALLOW` ne convient pas, car il
permet tout sauf ce qu'il cite.

Gardez le projet, l'étiquette `dsoxlab.lab=securite-seccomp`, la sonde et les
limites de ressources. N'ajoutez aucune capability, n'utilisez pas `privileged`
et ne modifiez pas le démon.
