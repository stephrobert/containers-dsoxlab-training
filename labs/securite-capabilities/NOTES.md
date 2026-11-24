# Les capabilities Linux

Linux découpe les pouvoirs de root en capabilities. Le sous-ensemble par défaut
de Docker est plus réduit que celui de root sur l'hôte, mais il peut encore
dépasser les besoins d'une application. `cap_drop` retire des pouvoirs, `cap_add`
rend ceux qui sont explicitement nécessaires. Il faut recréer le conteneur :
modifier Compose ne change pas un processus existant.

## Ce que le lab montre

Un lanceur confine ses travaux avec `chroot`. Mesuré sur `docker.lab`, le
2026-11-09, Docker Engine 29.9.2, Compose 5.6.1, le même service alpine dans cinq
configurations :

| Configuration | Le lanceur | Masque effectif de PID 1 |
| --- | --- | --- |
| défaut de Docker | fonctionne | `0xa80425fb` |
| tout retiré | **s'arrête au démarrage**, `chroot: can't change root directory: Operation not permitted` | `0x0` |
| tout retiré, une capability rendue (`CAP_SYS_CHROOT`) | fonctionne | `0x40000` |
| tout retiré, `CAP_CHOWN` rendue à la place | **s'arrête au démarrage** | `0x1` |
| tout retiré, `CAP_SYS_CHROOT` et `CAP_CHOWN` | fonctionne, **et un changement de propriétaire réussit** | `0x40001` |

La dernière ligne est le piège : un service qui marche avec une capability
superflue passe tous les tests fonctionnels. Seuls le masque effectif et un vrai
changement de propriétaire le distinguent du minimum.

## Une preuve n'est pas une seule chose

Ce qu'on a demandé à Docker (`HostConfig.CapDrop` et `CapAdd`), ce que le noyau
applique (`CapEff` dans `/proc/1/status`, un masque hexadécimal) et ce que le
conteneur peut encore faire sont trois preuves différentes. Les deux premières
peuvent diverger : Docker 29 écrit les noms avec leur préfixe `CAP_`.

## Ce que le lab n'accepte pas

- le mode privilégié, qui rend toutes les capabilities quoi que dise `cap_drop` ;
- une seconde capability, même d'apparence inoffensive : le lanceur n'en demande
  qu'une ;
- une liste de capabilities à retirer une par une, qui laisse passer ce qu'une
  image future ajouterait.

## À propos des ports

Une écoute réussie sur un port bas ne prouve rien sur `NET_BIND_SERVICE` : le
moteur pose `net.ipv4.ip_unprivileged_port_start=0` dans le conteneur, donc un
conteneur sans aucune capability écoute sur le port 80. Cette capability n'est
pas celle dont ce lab traite.

Voir [l'énoncé](challenge/README.fr.md). Le moteur doit déjà être disponible.
Setup et cleanup préservent les images préexistantes et la configuration du démon.
