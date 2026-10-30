# Une image a changé sous votre tag

## La situation

L'équipe livre une API d'inventaire sous l'étiquette `inventaire:1.0`. Cette
étiquette n'a pas bougé depuis trois semaines, et c'est précisément ce qui
rassure tout le monde : la version est figée, donc l'image l'est aussi.

Hier soir, la production a commencé à écrire un fichier que personne ne
reconnaît. L'étiquette, elle, affiche toujours `1.0`.

Sur cette machine, `inventaire:1.0` a été construite **deux fois**. La seconde
construction a pris la place de la première, sans que l'étiquette change d'un
caractère. C'est le comportement normal d'un tag : il désigne, il ne garantit
rien. Le `LABEL org.opencontainers.image.version` des deux images annonce
d'ailleurs `1.0` dans les deux cas, parce qu'une étiquette écrite dans l'image
ne vaut pas plus que celle écrite à l'extérieur.

## L'objectif

Dire exactement quelle image tourne, et le prouver autrement que par son nom.

Écrivez dans `/opt/lab-images/reponse.txt` trois lignes, une par entrée, sans
espace autour du signe égal :

```text
digest=<le digest de l'image que inventaire:1.0 désigne aujourd'hui>
base=<le digest de l'image debian:13 telle qu'elle est sur cette machine>
plateforme=<os/architecture de inventaire:1.0>
```

## Ce qui est noté

Quatre contrôles de poids égal, et aucun ne regarde vos commandes :

- le **digest annoncé** est celui que le tag désigne maintenant ;
- ce digest **n'est pas celui de la première construction**, dont la trace
  traîne encore dans `/opt/lab-images/digest-v1.txt`. La recopier ressemble à
  une réponse et ne mesure rien ;
- le **digest de l'image de base** est juste, et il est distinct de celui de
  l'image construite : une image et son socle ont deux identités ;
- la **plateforme** a la forme `os/architecture` et correspond à l'image.

Un chemin différent du nôtre qui atteint le même résultat vaut tout autant :
c'est l'état de votre fichier de réponse qui est noté, pas la façon d'y arriver.

## Ce dont vous disposez

Un hôte Debian 13 avec le démon Docker démarré, votre compte déjà membre du
groupe `docker`, et `skopeo`, qui sait lire une image **sans la lancer**.

## Deux pistes, si vous bloquez

Le digest d'une image locale ne se lit pas dans son tag : il vit dans les
métadonnées que le démon tient sur elle. Toute commande qui sait inspecter une
image sait le sortir.

Un digest commence par un nom d'algorithme, suivi de deux-points. Si votre
réponse n'en comporte pas, vous avez probablement recopié autre chose, par
exemple un identifiant court tronqué pour l'affichage.
