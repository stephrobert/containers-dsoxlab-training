# 79 Mo pour un script de trois cents octets

## La situation

Une image d'application pèse 79 Mo. On regarde ce qu'elle contient : un script
shell de trois cents octets, et quatre nombres dans un fichier.

Le reste est le socle. Une distribution complète, avec son gestionnaire de
paquets, sa bibliothèque C, ses pages de manuel, pour faire une addition.

Changer la ligne `FROM` prend une seconde. Et l'image ne démarre plus, sur un
message qui accuse le script.

## L'objectif

L'image `appli:lourde` marche : lancez-la, elle imprime son jeton, une somme et
un maximum. Pesez-la ensuite.

Un socle Alpine est déjà sur la machine, sous le nom `lab-socle-leger:1.0`, et
il pèse 8 Mo. Construisez `appli:legere` dessus.

```text
imprimer le même jeton, la même somme et le même maximum que appli:lourde
peser une fraction de appli:lourde
être construite sur le socle léger
CALCULER, et non réciter
```

Le contexte est dans `/opt/lab-migration/appli`. Ne modifiez pas
`appli:lourde` : c'est la référence à laquelle vous êtes comparé.

L'énoncé est aussi déposé dans `/opt/MISSION.md`.

## Changer la ligne `FROM` ne suffira pas

Essayez, et lisez le message.

```text
exec /usr/local/bin/traiter: no such file or directory
```

Par `sh`, il est encore plus net, et il porte le code 127 déjà rencontré :

```text
sh: /usr/local/bin/traiter: not found
```

Allez vérifier : le script est là, exécutable. **Ce n'est donc pas lui qui
manque.** Ce qui manque est l'interpréteur que son shebang réclame, et le noyau
rend l'erreur sous le nom du fichier qu'on lui a demandé.

C'est le même mécanisme que `troubleshoot-exit-127`, et la même famille de
message trompeur que `images-contexte-de-build` : **le moteur rend compte de ce
qu'il voit, pas de ce qui est.**

## Migrer, c'est adapter

Le script utilise deux constructions que son ancien socle lui donnait et que le
nouveau n'a pas. Aucun changement de `FROM` ne les y mettra.

Vous avez deux voies, et les deux passent les contrôles : réécrire ce qui
dépendait de l'ancien socle, ou installer sur le nouveau ce qui manque. La
première est celle que ce lab défend : ajouter un interpréteur de 2 Mo pour deux
constructions dont l'une tient en une boucle revient à payer le socle qu'on
vient de quitter.

## Ce qui est mesuré

| Socle | Taille |
| --- | --- |
| `debian:13-slim` | 78,9 Mo |
| `alpine:3.22` | 8,3 Mo, soit 9,5 fois moins |

Mesuré sur cette machine, le 2026-10-30. Et l'équivalent POSIX du script rend
le même résultat sur les deux socles : `somme=26 max=11` de part et d'autre.

## Ce qui est noté

L'**état du système**, et à quatre endroits qui ne se recouvrent pas : le
résultat sur les données du dépôt, le socle réellement utilisé (lu dans les
couches), le poids rapporté à la référence, et le calcul sur des données que
l'image **n'a jamais vues**.

Ce dernier contrôle est là parce que les trois autres passeraient sur une
application qui imprime un résultat figé. Les données du dépôt ne changent pas
pendant une session ; celles du contrôle, si.

Aucun seuil et aucun résultat n'est écrit dans le dépôt : les données sont
tirées à chaque passage, le résultat est recalculé à la notation, et le seuil de
poids est dérivé de l'image de référence.
