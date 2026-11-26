# Mémoire et OOM local au conteneur

`mem_limit` plafonne la RAM. `MemorySwap` de Docker représente le budget
combiné RAM et swap, pas le swap seul. Un `memswap_limit` égal à `mem_limit`
désactive le swap du conteneur si le noyau permet sa comptabilité.

Sur un projet neutre `demo-parser`, comparez `HostConfig.Memory` et
`MemorySwap` avec `memory.max` et `memory.swap.max` en cgroup v2.
Un budget combiné égal à la RAM donne un maximum swap de zéro. La mémoire
comprend les allocations anonymes, le cache de pages imputé et les pages tmpfs.

Le code 137 seul ne prouve pas un OOM : SIGKILL a d'autres causes. Une hausse du
compteur `oom_kill` dans `memory.events` prouve un OOM dans ce cgroup.
Une sonde exec peut mourir sans que Docker marque PID 1 comme `OOMKilled`.

L'exercice double une chaîne awk au plus 26 fois, uniquement dans un cgroup
vérifié de 32 Mio, avec une échéance de dix secondes et une garde mémoire hôte.
Aucun OOM hôte n'est recherché. Cgroup v2 et la comptabilité mémoire/swap sont
des prérequis. Voir [le challenge](challenge/README.fr.md).
