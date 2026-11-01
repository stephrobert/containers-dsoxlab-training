# seccomp

Seccomp filtre les numéros et arguments des syscalls, pas les chemins de fichiers.
Docker applique normalement un filtre par défaut. `seccomp:unconfined` retire
cette protection d'un conteneur sans modifier la politique du démon.

Un projet neutre `demo-counter` peut attacher un profil JSON via `security_opt`
dans Compose. `SCMP_ACT_ERRNO` refuse un appel avec une erreur au lieu de tuer
le processus. `errnoRet: 1` sélectionne EPERM. Une `defaultAction`
`SCMP_ACT_ALLOW` convient à un refus pédagogique ciblé, pas à une liste
d'autorisation de production.

Le filtre s'applique pendant l'initialisation OCI, avant le démarrage de
l'application. Refuser globalement `getppid` peut donc casser runc lui-même.
Une règle d'argument (`index: 0`, `op: SCMP_CMP_EQ`) limite le refus pédagogique
à `getpgid(2147483647)` et préserve les requêtes ordinaires sur les processus.

Recréez le service après modification. `Seccomp: 2` dans `/proc/1/status`
prouve que le filtrage est actif, pas que l'appel voulu est bloqué. Une sonde
de syscall apporte la seconde moitié de la preuve.

L'exercice compile sa sonde inoffensive avec les paquets Alpine ; un accès réseau
est nécessaire. Voir [le challenge](challenge/README.fr.md).
