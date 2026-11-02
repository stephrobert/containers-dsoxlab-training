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
