# Cahier des charges

Travaillez sur `docker.lab`, dans `/opt/dsoxlab-container-memoire-et-oom`.

1. Gardez `worker` actif dans le projet `dsoxlab-container-memoire-et-oom`,
   label `dsoxlab.lab=container-memoire-et-oom`.
2. Fixez la RAM et le budget combiné RAM-swap à 32 Mio chacun.
3. Gardez l'OOM killer actif ; `memory.max` doit valoir 33554432 et
   `memory.swap.max` doit valoir 0.
4. La sonde exec bornée du contrôle doit incrémenter oom_kill dans
   `memory.events`, tandis que PID 1 reste actif.

Gardez les garde-fous pids et CPU. Ni modification du swap hôte ni stress non borné.
