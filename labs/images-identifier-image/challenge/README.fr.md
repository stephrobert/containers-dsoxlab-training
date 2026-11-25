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

## Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable avec Docker démarré et `skopeo`
installé.

Le tag `inventaire:1.0` a été construit **deux fois** sur cette machine. La
seconde construction a pris la place de la première, sans que l'étiquette
change d'un caractère. Vous devez dire ce qui tourne vraiment.

L'énoncé est aussi déposé dans `/opt/lab-images/MISSION.md`.

### 1. Le digest de l'image que le tag désigne aujourd'hui

Celui de la **seconde** construction, la seule que `inventaire:1.0` désigne
maintenant.

Le digest de la première traîne encore dans
`/opt/lab-images/digest-v1.txt`. Le recopier est refusé : c'est la réponse de
surface, et un contrôle existe pour elle.

### 2. Le digest de l'image de base

Celui de `debian:13`, telle qu'elle est sur cette machine. Il est **distinct**
de celui de l'image construite : une image et son socle ont deux identités, et
confondre les deux est l'erreur que ce point mesure.

### 3. La plateforme de l'image

Sous la forme `os/architecture`, par exemple `linux/amd64`. Elle se lit sur
l'image, elle ne se devine pas depuis la machine.

### 4. Écrire la réponse

Trois lignes dans `/opt/lab-images/reponse.txt`, sans espace autour du signe
égal :

```text
digest=...
base=...
plateforme=...
```

Les lignes vides et les commentaires `#` sont tolérés, l'ordre est libre : le
contenu est noté, pas la mise en page.

### Ce qui n'est pas regardé

**Aucune commande n'est notée.** `docker image inspect`, `skopeo inspect` ou
une lecture du magasin d'images mènent au même état. Un chemin différent du
nôtre qui atteint le même résultat vaut tout autant.

Un `LABEL org.opencontainers.image.version` ne prouve rien non plus : les deux
images annoncent `1.0` à l'intérieur. Une étiquette écrite dans l'image ne
vaut pas plus que celle écrite à l'extérieur.

### Vérifier

```bash
dsoxlab check images-identifier-image
```
