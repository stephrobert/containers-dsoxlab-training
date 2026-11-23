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
4. Ce que l'image **ajoute à sa base** reste sous le budget que ce lab a
   mesuré sur cette machine, en construisant lui-même une référence pendant
   `dsoxlab run`. **Aucune base n'est imposée**, et celle que vous choisissez
   n'entre pas en compte : seul compte ce que vous posez dessus.
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

**Le budget de taille n'est pas un exercice d'optimisation.** Il est large, et
l'écart qu'il mesure est la taille de ce qui a été livré sans avoir de raison de
l'être. Mesuré sur cette machine : le contenu applicatif ajoute 0,1 Mo à sa base
quelle que soit cette base, et livrer le répertoire de travail en ajoute 80.

## Comment vous êtes noté

Six contrôles de poids égal, et **seul l'état final compte**. Aucune
instruction de Dockerfile n'est imposée : deux façons d'obtenir la même image
reçoivent la même note.

Le seuil est de **75 sur 100**. Une exigence ne se compense par aucun total :
**le jeton présent dans une couche fait échouer l'épreuve**, même avec tout le
reste en place. Un secret livré dans une image est un secret publié : l'image
part dans un registre, d'autres la lisent, et la retirer ensuite ne reprend
rien.

Quatre indices sont disponibles, et **ils coûtent des points** : `dsoxlab hint`.

## Épreuve : livrer une première image

Un dépôt porte une application, sa dépendance, un fichier d'identifiants et un
répertoire de travail. **Il n'y a pas de Dockerfile** : c'est à vous de l'écrire.

### Les six contrôles

Ils sont de poids égal, et chacun porte sur un fait vérifiable.

#### 1. L'image répond sans option d'identité

`docker run --rm premiere-livraison:1.0`, **sans `--user`**, rend la valeur
métier. Une image qui n'est exécutable qu'avec une option choisie par l'appelant
n'est pas livrable : celui qui la reçoit ne connaît pas ce détail.

#### 2. Un UID numérique non nul, propriétaire de ses données

**Numérique**, et non un nom : un nom ne se résout que dans l'image qui le
définit, et un orchestrateur ne lit pas son `/etc/passwd`. C'est la seule forme
qu'un tiers peut vérifier.

Et le répertoire des données **lui appartient**, sans être inscriptible par tous.
Déclarer un utilisateur non root et lui laisser un répertoire qu'il ne possède
pas livre une image qui échoue à sa première écriture ; le rendre inscriptible
par tous règle le symptôme en annulant le bénéfice.

#### 3. Le jeton dans aucune couche

**C'est l'exigence critique : elle n'est compensée par aucun total.**

Le contrôle lit **l'archive de l'image**, pas son système de fichiers. Un
`RUN rm` qui efface un secret à l'étape suivante laisse intacte la couche qui le
portait : le fichier a disparu de la vue finale, et il voyage toujours avec
l'image. Chercher dans le conteneur ne verrait rien et déclarerait propre une
image qui ne l'est pas.

Et c'est la **valeur** du jeton qui est cherchée, pas le nom du fichier :
renommer ne change rien au fait que le secret voyage.

Elle porte sur **ce seul fait**. Un secret publié est irréversible, et c'est le
défaut que cette épreuve existe pour éliminer.

#### 4. Le répertoire de travail n'est pas livré

Du gaspillage, et non une brèche : ce contrôle se note et **se compense**. Des
fichiers de travail alourdissent l'image de tous ceux qui la tirent,
définitivement, ce qui est une faute, mais une faute qui se rachète.

#### 5. Ce que l'image ajoute à sa base

**Aucune base n'est imposée**, et la vôtre n'entre pas en compte : le contrôle
compare ce que vous posez **par-dessus** avec ce qu'une image de référence pose
par-dessus la sienne, plus une marge.

Mesuré sur cette machine : le même contenu applicatif ajoute 0,1 Mo à
`alpine:3.22` comme à `debian:13-slim`, et livrer le répertoire de travail en
ajoute 80. C'est cet écart que le contrôle voit, et non la taille de votre base.

La marge est large. L'épreuve mesure « n'a pas livré ce qui n'a rien à faire
dans une image », pas « a optimisé au mégaoctet », qui est le sujet d'une autre
épreuve du parcours.

#### 6. Publiée, et le digest consigné est celui servi

Le digest est **demandé au registre**, puis comparé au vôtre. Un tag se
réécrit : deux `push` du même tag servent deux images différentes. Le digest est
la seule identité qu'un tiers puisse exiger.

Et il ne suffit pas qu'il corresponde : l'image est **tirée par ce digest**, puis
lancée sans option d'identité, et elle doit rendre la valeur métier. C'est le
geste de celui qui reçoit la livraison, joué pour de vrai : comparer deux
chaînes prouve que vous avez recopié le bon digest, pas que ce digest donne
quelque chose.

### Le barème

Six contrôles de poids égal, seuil à **75 sur 100**, et **seul l'état final
compte** : aucune instruction de Dockerfile n'est imposée.

Quatre indices, du plus vague au plus explicite, et **ils coûtent des points** :

```bash
dsoxlab hint
```
