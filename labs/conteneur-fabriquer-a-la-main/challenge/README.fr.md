# Un conteneur sans moteur

## 🧭 La situation

Sur `oci.lab`, une Debian 13 jetable, aucun moteur de conteneurs n'est
installé : ni Docker, ni Podman. L'équipe veut voir ce qu'est un conteneur
quand on retire le moteur, et vous demande d'en fabriquer un avec les seuls
outils du noyau.

Le dépôt `/srv/depot` porte deux copies de l'archive du système de fichiers
Alpine 3.24.2, dans `miroir-a/` et `miroir-b/`. L'une des deux a été altérée.
`/srv/depot/SHA256SUMS` contient la somme publiée par Alpine. Vous êtes `root`
par `sudo`.

## 🎯 Ce que vous devez obtenir

1. `/srv/atelier` contient le système de fichiers Alpine 3.24.2, extrait de
   l'archive **dont la somme SHA-256 correspond** à celle d'Alpine.
2. Un processus tourne avec `/srv/atelier` pour racine, dans ses **propres
   namespaces** `pid`, `uts`, `mnt`, `net` et `ipc`.
3. Dans ce conteneur, le nom de machine est **`atelier-isole`**, et l'hôte
   garde le sien.
4. Ce processus est le **PID 1** de son conteneur.
5. `/srv/atelier/dev/null` est un vrai **périphérique caractère** (1, 3).

Le conteneur doit **continuer de tourner après votre déconnexion** : les tests
le cherchent une fois votre session fermée.

## 🔎 Les repères utiles

`sha256sum -c` compare une archive à une somme attendue. Lancé depuis le
répertoire d'un miroir avec `../SHA256SUMS`, il dit si la copie est la bonne.
N'extrayez jamais une archive qui échoue.

La leçon montre la commande `unshare` qui crée les cinq namespaces et change la
racine. Un nouveau namespace `pid` ne s'applique qu'aux enfants : une option
est nécessaire pour que votre programme devienne le PID 1.

Pour qu'un processus survive à la fin de votre session, lancez-le détaché, par
exemple avec `setsid -f`, et faites-lui exécuter une commande qui dure
(`sleep infinity`).

Le `/dev` du rootfs est vide. `mknod` crée un périphérique : `c` pour un
périphérique caractère, puis ses deux numéros.

## ✅ Comment vous saurez que c'est bon

Les tests interrogent le noyau de `oci.lab` : ils cherchent un processus dont
la racine est `/srv/atelier`, comparent ses namespaces à ceux de l'hôte,
lisent son nom de machine avec `nsenter` et son numéro dans son namespace, et
vérifient l'empreinte du `busybox` extrait et la nature de `/dev/null`.

```bash
dsoxlab check conteneur-fabriquer-a-la-main
```
