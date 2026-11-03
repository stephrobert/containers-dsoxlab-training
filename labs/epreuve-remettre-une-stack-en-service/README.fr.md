# Remettre une stack Compose en service

Ce lab mesure une composition à deux services : le projet nommé et ses deux
services debout, un frontal qui joint ses données **par leur nom de service**
sur un réseau de la pile, une seule façade publiée sur la boucle locale, une
donnée qui survit à la recréation de la pile, et une configuration dont au
moins une valeur vient d'une interpolation.

L'exigence critique est la **donnée écrite avant une recréation et servie
après** : c'est la seule chose qu'une composition perd pour de bon.

## Ce que ce lab n'exige pas, et pourquoi

Ni sonde de santé, ni condition de dépendance. Toutes deux s'enseignent au
module suivant, et une épreuve ne note pas ce que la leçon n'a pas présenté.

Elle n'en a pas besoin : le frontal fourni réessaie son amont pendant une
minute, donc l'ordre de démarrage est indifférent. Ce n'est pas un
renoncement, c'est une autre façon de s'en passer, et elle se mesure aussi
bien.

Lancez le nettoyage normal avant de rejouer le lab. Il retire uniquement les
conteneurs, réseaux, volumes et l'image portant les labels de ce lab.
