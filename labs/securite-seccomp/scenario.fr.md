# Un syscall inoffensif comme frontière mesurable

La politique de démonstration doit refuser `getpgid(2147483647)` avec EPERM
tout en autorisant `getpgid(0)` et `getpid`. Le PID réservé cible seulement
la sonde inoffensive, pas l'initialisation du runtime. Sans filtre, interroger
ce PID inexistant renvoie ESRCH, pas EPERM.
La sonde C fournie effectue seulement ces appels en lecture et affiche leur verdict.

Dans `/opt/dsoxlab-securite-seccomp`, attachez un filtre seccomp explicite à
`worker` dans le projet `dsoxlab-securite-seccomp`. Le JSON fourni autorise
actuellement tout et le starter utilise explicitement `unconfined`.

C'est une leçon contrôlée sur les syscalls, pas un profil de production.
Ne changez jamais les valeurs par défaut du démon et n'utilisez pas privileged.
