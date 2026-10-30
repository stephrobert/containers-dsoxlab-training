# Le Dockerfile marche, et c'est bien le problème

## La situation

L'intégration continue met six minutes à construire une image, et personne ne
comprend pourquoi : la dernière modification tenait en une ligne de code.

On regarde le Dockerfile. Il est court, lisible, et il **marche** : l'image
produite est juste, l'application tourne. Rien n'a l'air cassé, donc rien ne
semble à corriger, et c'est pour cela que ce défaut vit des années dans un
dépôt.

Puis on construit deux fois de suite en changeant une ligne entre les deux, et
on voit l'installation des dépendances se rejouer en entier. Elle n'a pas
changé. Elle est refaite parce qu'une instruction placée avant elle a changé.

## L'objectif

Le contexte de construction est dans `/opt/lab-couches/appli`. Le Dockerfile
qui s'y trouve marche : construisez-le, l'image est juste.

**Mesurez ensuite ce qu'il coûte.** Construisez une première fois, changez une
ligne de `src/main.sh`, reconstruisez, et regardez le temps que passe
l'installation. Elle coûte une seconde par dépendance, et elle en a trois.

Réordonnez les instructions pour que ce travail soit :

```text
servi par le cache   quand le CODE change
refait               quand le MANIFESTE change
```

Les deux moitiés comptent. Un cache qui sert toujours est une faute aussi grave
qu'un cache qui ne sert jamais : l'image resterait figée sur d'anciennes
dépendances, et personne ne le verrait avant la production.

Et ne faites pas entrer dans l'image ce qui n'a rien à y faire : le contexte
porte un brouillon et le Dockerfile lui-même, qu'une copie du contexte entier
embarque sans rien demander.

Construisez l'image finale sous le nom `appli:ordonnee`. Elle doit imprimer son
jeton quand on la lance, et porter les trois dépendances déclarées.

L'énoncé est aussi déposé dans `/opt/MISSION.md`.

## La règle qui sort de ce lab

**Chaque instruction dépend de ce qui la précède, et de rien d'autre.** Le cache
sert une couche tant que tout ce qui est au-dessus d'elle est inchangé.

D'où l'ordre : ce qui change rarement en haut, ce qui change à chaque commit en
bas, et chaque travail coûteux placé juste après ce dont il dépend, seul. Le
manifeste des dépendances se copie donc **seul**, avant l'installation, et le
code **après** elle.

## Ce qui est noté

L'**état du système**, et il est mesuré par l'effet. Les contrôles reconstruisent
l'image dans une **copie** du contexte, une fois avec une ligne de code en plus,
une fois avec une dépendance en plus, et comparent une empreinte que l'outil
d'installation laisse dans l'image. Deux images qui portent la même empreinte
n'ont pas rejoué l'installation.

Votre répertoire de travail n'est pas touché, et aucun chemin n'est imposé : un
fichier d'exclusion et une copie ciblée donnent le même état, et c'est l'état
qui compte.
