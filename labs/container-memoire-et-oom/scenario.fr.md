# Un OOM limité à un seul cgroup

Le worker démarre avec un plafond sûr de 96 Mio. Le contrat de déploiement
impose plutôt 32 Mio de RAM, sans swap, avec l'OOM killer actif.

Dans `/opt/dsoxlab-container-memoire-et-oom`, appliquez ce budget à `worker`
dans le projet `dsoxlab-container-memoire-et-oom`. Une sonde d'allocation bornée
doit être tuée dans le cgroup du conteneur, tandis que son petit PID 1 survit.

Le contrôle vérifie les deux limites et la marge hôte avant d'allouer. Il observe
`memory.events`, pas un code de sortie supposé. Ne stressez pas l'hôte, ne
désactivez pas l'OOM killer, ne changez pas le swap hôte et n'utilisez pas
d'allocateur non borné.
Le même PID 1 doit rester actif sans redémarrage, et un reçu applicatif frais
doit rester lisible après l'incident. L'essai retire seulement son propre reçu ;
cette conservation pendant l'incident ne garantit pas la survie à un reboot.
