# images-migrer-vers-alpine : changer de socle n'est pas changer une ligne

## Ce que ce lab éprouve

Qu'une application dépend de ce que son socle lui donne, et que le message qui
le lui rappelle **ne nomme pas la cause**. Le fichier existe, le moteur dit
qu'il est introuvable, et c'est l'interpréteur de son shebang qui manque.

## Mesuré avant d'être écrit

Sur `docker.lab`, le 2026-10-30 :

| Socle | Taille |
| --- | --- |
| `debian:13-slim` | 78,9 Mo |
| `alpine:3.22` | 8,3 Mo, soit **9,5 fois moins** |

Le même script, en entrypoint sur Alpine : `exec /src/traiter.sh: no such file
or directory`. Lancé par `sh` : `not found`, code **127**. Et le fichier :
`-rwxr-xr-x 205 octets`, parfaitement présent.

L'équivalent POSIX rend le même résultat sur les deux socles, mesuré :
`somme=26 max=11` de part et d'autre.

## Pourquoi ce lab relie trois autres

Le code 127 est celui de `troubleshoot-exit-127` : un fichier trouvé mais
inexécutable, ou un interpréteur absent. Le message trompeur est celui de
`images-contexte-de-build` : le moteur rend compte de ce qu'il voit, pas de ce
qui est. Et le gain de poids est le même sujet que
`images-optimiser-la-taille`, par l'autre bout : ce lab-là allège ce qu'on
ajoute, celui-ci allège ce dont on part.

Un apprenant qui a joué les trois reconnaît le mécanisme avant de lire l'indice.

## Pourquoi quatre contrôles qui ne se recouvrent pas

Le premier éprouve le résultat sur les données du dépôt. Le deuxième lit le
socle **dans les couches** : une image peut marcher et peser le bon poids sans
avoir changé de base. Le troisième pèse, contre la référence.

Le quatrième est le seul qui attrape une application qui **récite** : il lui
monte des données qu'elle n'a jamais vues et recalcule ce qu'elle doit rendre.
Les trois autres passeraient sur une image qui imprime un résultat figé, puisque
les données du dépôt ne changent pas pendant une session.

## Pourquoi le socle est lu dans les couches

Chercher `/etc/alpine-release` serait plus court, et plus fragile : c'est une
convention de distribution, et elle ne dit rien d'une image reconstruite depuis
un autre socle qui porterait le même fichier.

Les couches, elles, sont la chose même : celles du socle léger doivent être le
préfixe de celles de l'image. C'est la même mesure que le contrôle
anti-aplatissement de `images-optimiser-la-taille`, et pour la même raison.

## Pourquoi les deux voies sont acceptées

Réécrire le script en sh POSIX, ou installer bash sur le socle léger : les deux
passent les quatre contrôles.

C'est délibéré. Le lab **défend** la première, dans son énoncé et dans sa
solution de référence : ajouter un interpréteur de 2 Mo pour deux constructions
dont l'une tient en une boucle revient à payer le socle qu'on vient de quitter.
Mais il ne la **note** pas, parce que la seconde est un choix légitime quand le
script est long, et qu'un contrôle qui l'interdirait noterait une opinion.

Le catalogue a un endroit où une opinion est notée, dans
`troubleshoot-permission-refusee`, et c'est parce qu'un lab de méthode avait
déjà tranché. Ici, rien n'a tranché.

## Aucun résultat, aucun seuil n'est écrit

Les données sont tirées par le setup à chaque passage, le résultat est recalculé
à la notation, et le plafond de poids est dérivé de l'image de référence pesée
au même moment.

C'est aussi la raison pour laquelle le setup **construit** `appli:lourde` : sans
cette référence, il faudrait écrire un seuil dans le dépôt, qui serait faux au
premier changement de socle.

## Un détail d'écriture qui a été corrigé

Les données étaient d'abord écrites par un `join('\n')` dans un bloc littéral
YAML, ce qui dépend de deux couches d'échappement, YAML puis Jinja, dont la
règle change avec le style du scalaire. Une boucle explicite ne dépend d'aucune
des deux, et son rendu a été **éprouvé sur le Jinja qui joue réellement le
playbook**, celui que `dsoxlab` embarque.

## L'état de départ est cassé, et c'est la règle du dépôt

`appli:legere` n'existe pas : les quatre contrôles sont faux avant tout travail.
Une tâche du setup vérifie que la référence marche, que l'image de l'apprenant
n'existe pas, et que le socle léger est bien là.

## Un piège du cleanup, payé d'avance

L'image de référence part avec le reste. Les contrôles s'y comparent, en taille
comme en résultat : la laisser derrière ferait comparer le travail d'un passage
à la référence d'un autre, dont les données tirées au hasard ne sont plus les
mêmes.

## Ce que le lab n'exige pas

Un chemin. Le script se réécrit ou le socle se complète, le Dockerfile se
modifie ou se double. Le jeton et les données sont tirés par le setup : rien
n'est écrit en dur dans les contrôles.
