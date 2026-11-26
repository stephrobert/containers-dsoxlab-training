# Un veilleur qui ne touche à rien

## La situation

Sur `oci.lab`, une Debian 13 sans moteur de conteneurs, l'équipe veut un
conteneur `veilleur` qui tourne en permanence, lancé directement par runc. Un
premier essai a été fait : il s'est arrêté, et il occupe toujours
l'identifiant.

L'image busybox 1.37.0 est prête dans le layout `/srv/oci-busybox`, sous le
tag `1.37.0`. runc, umoci, skopeo et jq sont installés. Vous êtes `root` par
`sudo`.

## Ce que vous devez obtenir

1. Le bundle **`/srv/veilleur`** est tiré de l'image de `/srv/oci-busybox`.
   Son `config.json` lance **`sleep infinity`**, pose le nom de machine
   **`veilleur`**, et rend la racine **en lecture seule**.
2. Le conteneur **`veilleur`** tourne depuis ce bundle, détaché : il continue
   après votre déconnexion.
3. Vu de l'intérieur, il porte le nom `veilleur`, et une écriture à sa racine
   est refusée.
4. Plus aucun conteneur arrêté ne reste dans `runc list`.

## Les repères utiles

La leçon fabrique un bundle de deux façons : à la main avec `runc spec`, ou
depuis une image avec `umoci unpack`. Ici, partez de l'image. Attention : le
`config.json` qu'écrit umoci ne rend pas la racine en lecture seule, celui de
`runc spec` si.

Un conteneur détaché demande `process.terminal` à `false`. Un conteneur arrêté
garde son identifiant tant qu'il n'a pas été supprimé.

## Comment vous saurez que c'est bon

Les tests lisent `/srv/veilleur/config.json`, l'état que runc donne pour
`veilleur`, la liste de ses conteneurs, et jouent `hostname` et une écriture
dans le conteneur avec `runc exec`.

```bash
dsoxlab check runtime-lancer-un-bundle
```
