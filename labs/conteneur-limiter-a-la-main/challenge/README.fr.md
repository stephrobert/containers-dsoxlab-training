# Un conteneur qui ne déborde pas

## 🧭 La situation

Sur `oci.lab`, une Debian 13 sans moteur de conteneurs, le conteneur fabriqué
à la main au lab précédent a montré ses limites : il voit peu, mais il peut
consommer toute la machine, et son root garde tous ses pouvoirs. L'équipe vous
demande de le contenir avec les seuls outils du noyau.

Le système de fichiers Alpine 3.24.2 est prêt dans `/srv/quai`, avec
`/dev/null` et `/dev/zero`. Vous êtes `root` par `sudo`.

## 🎯 Ce que vous devez obtenir

1. Un cgroup **`/sys/fs/cgroup/quai`** plafonne la mémoire à **48M**, sans
   swap (`memory.swap.max` à `0`).
2. Le même cgroup plafonne le nombre de tâches à **32** et le CPU à **30 %**
   d'un cœur, sur une période de 100 ms.
3. Un conteneur tourne avec `/srv/quai` pour racine, dans son propre namespace
   `pid`, et **tous ses processus** sont dans le cgroup `quai`.
4. Le root de ce conteneur a perdu **`CAP_SYS_ADMIN`** : il ne peut plus
   changer le nom de machine.
5. Le plafond mémoire a **déjà tué** au moins un processus du cgroup `quai`.

Le conteneur doit **continuer de tourner après votre déconnexion** : les tests
le cherchent une fois votre session fermée.

## 🔎 Les repères utiles

Un cgroup se crée avec `mkdir` sous `/sys/fs/cgroup`, et chaque plafond
s'écrit dans un fichier de réglage. Un processus rejoint le groupe en écrivant
son numéro dans `cgroup.procs`, et ce qu'il lance ensuite en hérite.

La leçon place le conteneur dans son cgroup dès sa naissance, et retire des
capabilities avec `setpriv`, entre `unshare` et `chroot`. Ici, le conteneur
doit en plus tourner détaché : `setsid -f` le lance sans terminal et vous rend
la main.

Pour le dernier point, lancez dans le cgroup `quai` un programme qui grossit en
mémoire. Le compteur `oom_kill` de `memory.events` garde la trace de ce que le
noyau a tué.

## ✅ Comment vous saurez que c'est bon

Les tests lisent les fichiers de réglage du cgroup `quai` et son compteur
`oom_kill`. Ils cherchent les processus dont la racine est `/srv/quai`, et
lisent leur cgroup, leur namespace `pid` et leurs masques de capabilities dans
`/proc`.

```bash
dsoxlab check conteneur-limiter-a-la-main
```
