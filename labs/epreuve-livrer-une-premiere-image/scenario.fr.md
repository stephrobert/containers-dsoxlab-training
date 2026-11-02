# Livrer une première image publiable

Une petite application attend d'être livrée. Elle vit dans
`/opt/lab-premiere-livraison`, avec tout ce que son auteur y a laissé : son
code, sa dépendance, le fichier d'identifiants qui lui servait à récupérer ses
paquets, et le répertoire de travail où il entassait ses extraits.

**Il n'y a pas de Dockerfile.** C'est à vous de l'écrire.

Le registre du lab est déjà en marche sur `127.0.0.1:5000`. Il accepte le HTTP,
parce qu'il écoute sur la boucle locale : il n'y a rien à configurer sur le
démon.

## Ce qui est attendu à la fin

1. L'image **`premiere-livraison:1.0`** existe, et
   `docker run --rm premiere-livraison:1.0`, **sans aucune option d'identité**,
   rend la ligne `inventaire=` suivie de la donnée du fichier
   `donnees/reference`.
2. L'image **ne tourne pas en root** : l'utilisateur qu'elle déclare est un
   **UID numérique non nul**, et le répertoire des données dans l'image **lui
   appartient**, sans être inscriptible par tous.
3. Ni le fichier `.identifiants`, ni son jeton, ni le contenu de `travail/` ne
   se trouvent dans **aucune couche** de l'image.
4. La taille de l'image reste **sous le seuil que ce lab a mesuré** sur cette
   machine, en construisant lui-même une référence pendant `dsoxlab run`.
5. L'image est **publiée** dans le registre du lab, et le **digest que le
   registre sert** est consigné dans
   `/opt/lab-premiere-livraison/digest.txt`, sur une seule ligne, sous la forme
   `sha256:...`.

L'énoncé complet est aussi sur la machine, dans
`/opt/lab-premiere-livraison/MISSION.md`.

## Deux précisions qui comptent

**L'UID est libre**, pourvu qu'il soit numérique et non nul. Ce qui est mesuré
n'est pas le chiffre, c'est qu'il soit numérique : un nom d'utilisateur ne se
résout que dans l'image qui le définit, et un orchestrateur ne lit pas son
`/etc/passwd`.

**Le seuil de taille n'est pas un exercice d'optimisation.** Il est large, et
l'écart qu'il mesure est la taille de ce qui a été livré sans avoir de raison de
l'être.

## Comment vous êtes noté

Cinq contrôles de poids égal, et **seul l'état final compte**. Aucune
instruction de Dockerfile n'est imposée : deux façons d'obtenir la même image
reçoivent la même note.

Le seuil est de **75 sur 100**. Une exigence ne se compense par aucun total :
**le jeton présent dans une couche fait échouer l'épreuve**, même avec tout le
reste en place. Un secret livré dans une image est un secret publié : l'image
part dans un registre, d'autres la lisent, et la retirer ensuite ne reprend
rien.

Quatre indices sont disponibles, et **ils coûtent des points** : `dsoxlab hint`.
