# Épreuve : livrer une première image

Un dépôt porte une application, sa dépendance, un fichier d'identifiants et un
répertoire de travail. **Il n'y a pas de Dockerfile** : c'est à vous de l'écrire.

## Les six contrôles

Ils sont de poids égal, et chacun porte sur un fait vérifiable.

### 1. L'image répond sans option d'identité

`docker run --rm premiere-livraison:1.0`, **sans `--user`**, rend la valeur
métier. Une image qui n'est exécutable qu'avec une option choisie par l'appelant
n'est pas livrable : celui qui la reçoit ne connaît pas ce détail.

### 2. Un UID numérique non nul, propriétaire de ses données

**Numérique**, et non un nom : un nom ne se résout que dans l'image qui le
définit, et un orchestrateur ne lit pas son `/etc/passwd`. C'est la seule forme
qu'un tiers peut vérifier.

Et le répertoire des données **lui appartient**, sans être inscriptible par tous.
Déclarer un utilisateur non root et lui laisser un répertoire qu'il ne possède
pas livre une image qui échoue à sa première écriture ; le rendre inscriptible
par tous règle le symptôme en annulant le bénéfice.

### 3. Le jeton dans aucune couche

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

### 4. Le répertoire de travail n'est pas livré

Du gaspillage, et non une brèche : ce contrôle se note et **se compense**. Des
fichiers de travail alourdissent l'image de tous ceux qui la tirent,
définitivement, ce qui est une faute, mais une faute qui se rachète.

### 5. Ce que l'image ajoute à sa base

**Aucune base n'est imposée**, et la vôtre n'entre pas en compte : le contrôle
compare ce que vous posez **par-dessus** avec ce qu'une image de référence pose
par-dessus la sienne, plus une marge.

Mesuré sur cette machine : le même contenu applicatif ajoute 0,1 Mo à
`alpine:3.22` comme à `debian:13-slim`, et livrer le répertoire de travail en
ajoute 80. C'est cet écart que le contrôle voit, et non la taille de votre base.

La marge est large. L'épreuve mesure « n'a pas livré ce qui n'a rien à faire
dans une image », pas « a optimisé au mégaoctet », qui est le sujet d'une autre
épreuve du parcours.

### 6. Publiée, et le digest consigné est celui servi

Le digest est **demandé au registre**, puis comparé au vôtre. Un tag se
réécrit : deux `push` du même tag servent deux images différentes. Le digest est
la seule identité qu'un tiers puisse exiger.

Et il ne suffit pas qu'il corresponde : l'image est **tirée par ce digest**, puis
lancée sans option d'identité, et elle doit rendre la valeur métier. C'est le
geste de celui qui reçoit la livraison, joué pour de vrai : comparer deux
chaînes prouve que vous avez recopié le bon digest, pas que ce digest donne
quelque chose.

## Le barème

Cinq contrôles de poids égal, seuil à **75 sur 100**, et **seul l'état final
compte** : aucune instruction de Dockerfile n'est imposée.

Quatre indices, du plus vague au plus explicite, et **ils coûtent des points** :

```bash
dsoxlab hint
```
