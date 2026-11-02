# Épreuve : livrer une première image

Un dépôt porte une application, sa dépendance, un fichier d'identifiants et un
répertoire de travail. **Il n'y a pas de Dockerfile** : c'est à vous de l'écrire.

## Les cinq contrôles

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

### 3. Ni le jeton ni le travail dans aucune couche

**C'est l'exigence critique : elle n'est compensée par aucun total.**

Le contrôle lit **l'archive de l'image**, pas son système de fichiers. Un
`RUN rm` qui efface un secret à l'étape suivante laisse intacte la couche qui le
portait : le fichier a disparu de la vue finale, et il voyage toujours avec
l'image. Chercher dans le conteneur ne verrait rien et déclarerait propre une
image qui ne l'est pas.

Et c'est la **valeur** du jeton qui est cherchée, pas le nom du fichier :
renommer ne change rien au fait que le secret voyage.

### 4. La taille sous le seuil mesuré

Le seuil vient d'une **construction de référence faite sur cette machine**
pendant `dsoxlab run`. Il n'est pas écrit dans le test : une taille en dur
périmerait à la première mise à jour de l'image de base, et le lab se mettrait à
refuser du travail juste.

La marge est large. L'épreuve mesure « n'a pas livré ce qui n'a rien à faire
dans une image », pas « a optimisé au mégaoctet ».

### 5. Publiée, et le digest consigné est celui servi

Le digest est **demandé au registre**, puis comparé au vôtre. Un tag se
réécrit : deux `push` du même tag servent deux images différentes. Le digest est
la seule identité qu'un tiers puisse exiger.

## Le barème

Cinq contrôles de poids égal, seuil à **75 sur 100**, et **seul l'état final
compte** : aucune instruction de Dockerfile n'est imposée.

Quatre indices, du plus vague au plus explicite, et **ils coûtent des points** :

```bash
dsoxlab hint
```
