# Resserrer le profil du moteur, et non le remplacer

La politique de votre équipe doit refuser `getpgid(2147483647)` avec EPERM tout
en autorisant `getpgid(0)` et `getpid`. L'argument de PID réservé ne vise que la
sonde inoffensive, pas l'initialisation du runtime. Sans filtre, interroger ce
PID inexistant rend ESRCH et non EPERM : les deux erreurs diffèrent, et une seule
prouve que le filtre a mordu. La sonde C fournie n'effectue que ces appels en
lecture et affiche leur verdict.

**Partez du profil par défaut du moteur, pas d'une page blanche.** Un profil dont
le `defaultAction` vaut `SCMP_ACT_ALLOW` permet tout sauf les lignes qu'il
refuse : c'est une liste noire et non une politique, et ce n'est jamais ce qu'un
service doit porter. `assets/seccomp-defaut.json`, recopié dans l'espace de
travail du lab, est le profil de référence. Dérivez-le : sortez `getpgid` de sa
liste d'autorisation massive, puis réautorisez-le pour tout argument sauf celui
qui est réservé.

Il faut deux règles et non une, et elles doivent être mutuellement exclusives.
Un `SCMP_ACT_ERRNO` sur l'argument réservé posé à côté d'un `SCMP_ACT_ALLOW`
inconditionnel ne mord pas : c'est l'autorisation qui gagne, et l'appel atteint
le noyau. Utilisez `SCMP_CMP_EQ` pour refuser et `SCMP_CMP_NE` pour autoriser.

Dans `/opt/dsoxlab-securite-seccomp`, attachez votre profil dérivé à `worker`
dans le projet `dsoxlab-securite-seccomp`. Le starter emploie explicitement
`unconfined`. Tout ce que le profil par défaut refuse déjà doit rester refusé,
donc n'ajoutez aucune capacité : `unshare` n'y est permis que pour les conteneurs
qui détiennent `CAP_SYS_ADMIN`.

Le profil de référence est une copie épinglée de `moby/profiles`
(`seccomp/v0.3.0`), car le moteur embarque le sien dans son binaire : il n'existe
aucun fichier à relever sur l'hôte. Ce que vous durcissez est donc cette copie,
et non le profil vivant du démon.

Ne changez jamais les valeurs par défaut du démon et n'utilisez pas privileged.
