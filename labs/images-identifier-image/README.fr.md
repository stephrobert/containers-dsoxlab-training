# images-identifier-image : le tag ment, le digest non

## Ce que ce lab éprouve

Dire quelle image tourne vraiment. Pas celle que le tag annonce : celle que le
moteur a réellement chargée. C'est le premier geste de toute la chaîne
d'approvisionnement, et c'est celui qui manque le plus souvent, parce qu'un
tag a l'air d'une identité.

Il est noté sur le **contenu d'un fichier de réponse**, jamais sur les
commandes tapées. `docker image inspect`, `skopeo inspect` ou une lecture du
magasin d'images mènent au même état : noter la commande reviendrait à noter
un style.

## Le piège, et il est construit

Le setup construit **deux images différentes sous le même tag**
`inventaire:1.0`, l'une après l'autre. La seconde prend la place de la
première sans que l'étiquette change d'un caractère, parce que c'est le
comportement normal d'un tag : il désigne, il ne garantit rien.

Le `LABEL org.opencontainers.image.version` des deux images annonce `1.0` dans
les deux cas. Une étiquette écrite **dans** l'image ne vaut pas plus que celle
écrite à l'extérieur, et c'est contre-intuitif pour qui découvre OCI.

Le digest de la première construction reste visible dans
`/opt/lab-images/digest-v1.txt`. Le recopier ressemble à une réponse, et l'un
des quatre contrôles existe précisément pour le refuser : c'est le cas négatif
que le contrat `conteneurs-11` du pilotage demande de rejeter.

## Ce qui est noté

Quatre contrôles de poids égal :

- le digest annoncé est celui que le tag désigne **maintenant** ;
- ce digest n'est **pas** celui de la première construction ;
- le digest de l'image de base est juste, et **distinct** de celui de l'image
  construite : une image et son socle ont deux identités ;
- la plateforme a la forme `os/architecture` et correspond à l'image.

## Ce qu'il ne couvre pas

La publication dans une registry et le `pull` par digest, qui appartiennent au
module `images-distribution`. L'épinglage dans un Dockerfile et dans un
manifeste, qui est un geste d'écriture et non de lecture. La signature, qui
prouve l'origine quand le digest ne prouve que l'identité.

## Ce dont vous disposez

Une Debian 13 jetable, montée par `dsoxlab provision`, avec le démon Docker
démarré, votre compte déjà membre du groupe `docker`, et `skopeo`, qui sait
lire une image **sans la lancer**. Rien n'est installé sur votre poste.

## Durée

30 minutes. Les indices coûtent de 10 à 25 points.

Le guide : [https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/ecrire-dockerfile/](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/ecrire-dockerfile/)
