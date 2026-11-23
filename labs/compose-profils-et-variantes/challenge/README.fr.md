# Scénario

L'équipe a un seul fichier Compose, et deux façons de s'en servir. En
développement, les sources sont montées dans le conteneur : on édite, on
recharge, on ne reconstruit pas. En déploiement, rien n'est monté, et l'image
porte tout.

Depuis six mois, les deux usages cohabitent dans le même fichier, avec des
lignes commentées qu'on décommente « juste le temps d'un essai ».

Le mois dernier, une mise en production est partie avec le montage encore actif.
Le service lisait un répertoire de l'hôte qui n'existait pas sur la machine de
production : il a démarré, répondu, et servi une version vieille de trois
semaines. Personne ne l'a vu pendant deux jours, parce que le fichier, lui,
avait l'air juste.

On vous demande de séparer les deux usages pour de bon, et de ne plus rien
laisser au décommentage.

## Mission

Dérivez du fichier de base une variante de développement qui monte les sources,
et une variante de déploiement qui n'en monte aucune. Laissez la seconde en
service.

Le fichier de base ne se modifie pas. Le détail de ce qui est attendu est dans
`/opt/lab-variantes/MISSION.md`.

## Ce qui est demandé

Sur `docker.lab`, une Debian 13 jetable. Dans `/opt/lab-variantes`, un fichier
de base `compose.yaml` **que vous ne modifiez pas**, et deux choses qui ne
disent pas la même version :

- l'**image** porte sa propre `version.txt`, figée à la construction ;
- le **disque** porte `src/version.txt`, avec une autre valeur.

Le service rend la version qu'il lit sur `/app/src/version.txt`. C'est tout
l'appareil de mesure : sa réponse dit sans ambiguïté s'il lit l'image ou le
disque de l'hôte.

Il écoute sur `127.0.0.1:18081`.

### 1. Une variante de développement, qui monte les sources

Écrivez `/opt/lab-variantes/compose.dev.yaml`, à **dériver** du fichier de base
et non à recopier. Elle monte `/opt/lab-variantes/src` sur `/app/src` dans le
conteneur, de sorte qu'une modification du disque se voie sans reconstruire.

### 2. Une variante de déploiement, qui n'en monte aucun

Écrivez `/opt/lab-variantes/compose.deploiement.yaml`, dérivée du même fichier
de base. Elle ne monte **rien** : le service y lit la version de l'image.

Un montage de développement oublié en déploiement est l'incident classique. Il
ne se voit pas dans le fichier de base, il se voit dans la **configuration
effective**, et c'est là que le contrôle regarde.

### 3. Le déploiement, debout

Laissez la variante de **déploiement** en service, dans le projet Compose
`dsoxlab-variantes`. C'est l'état final attendu, et le service doit y répondre
la version de l'**image**.

### 4. Le service optionnel, sous son profil

Le fichier de base déclare un service `debug` sous le profil `debug`. Vérifiez
qu'il reste **absent** de la configuration effective des deux variantes tant que
ce profil n'est pas demandé, et **présent** dès qu'il l'est.

Vous n'avez rien à écrire pour cela : vous avez à ne pas le casser en dérivant.

### L'état final attendu

La variante de déploiement tourne, sans aucun montage, et sert la version de
l'image. Les deux fichiers de variante existent, dérivent du fichier de base, et
le fichier de base est inchangé.

### Ce qui n'est pas noté

La façon dont vous dérivez : `include`, `extends`, plusieurs `-f`, ou un
`COMPOSE_FILE`. Le contrôle lit la configuration effective, qui est la seule
chose qui compte, et jamais la commande que vous avez tapée.
