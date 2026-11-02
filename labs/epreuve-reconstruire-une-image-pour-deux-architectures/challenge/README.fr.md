# Épreuve : reconstruire une image pour deux architectures

Une image qui marche, en une seule étape, avec son compilateur, son jeton dans
l'historique, et une seule architecture. Tout est à reprendre **dans une seule
image**.

## Les cinq contrôles

Ils sont de poids égal, et chacun porte sur un fait vérifiable. **Ils portent sur
l'image tirée du registre**, parce que publier sans rien garder en local est la
façon normale de faire.

### 1. Ni compilateur ni gestionnaire de paquets dans l'image publiée

Ils n'ont servi qu'à construire, et ils voyagent ensuite chez tous ceux qui
tirent l'image.

**Et la charge métier réussit.** Retirer le compilateur est facile ; le retirer
en gardant un binaire qui fonctionne est le geste du multi-étapes. Un binaire lié
dynamiquement contre des bibliothèques restées dans l'étape de construction ne
démarre pas : c'est l'erreur classique.

### 2. La taille sous le seuil mesuré

Le seuil vient d'une construction de référence **multi-étapes** faite sur cette
machine pendant `dsoxlab run`. Il n'est pas écrit dans le test : une taille en
dur périmerait à la première mise à jour de l'image de base.

### 3. Le jeton nulle part, et la dépendance présente

**C'est l'exigence critique : elle n'est compensée par aucun total.**

Deux endroits distincts. **L'historique** : un `--build-arg` y laisse la valeur,
et quiconque tire l'image la relit. Mesuré sur le banc de cette épreuve : deux
occurrences avec `--build-arg`, zéro avec un secret monté. **Les couches**, parce
qu'un secret écrit dans un fichier puis effacé voyage toujours dans la couche qui
le portait.

**Et la dépendance doit être là** : retirer le jeton sans s'en servir donne une
image propre et inutile.

### 4. L'index porte les deux architectures, et chacune s'exécute

Le contrôle cherche `amd64` et `arm64` **parmi** les manifestes, sans en exiger
un nombre : l'outil de construction ajoute ses attestations, qui se présentent
comme des plateformes `unknown`.

**Et chacune s'exécute.** Un index qui déclare une plateforme dont l'image ne
démarre pas est pire qu'un index à une seule entrée : il promet un déploiement
qui échouera chez celui qui s'y fie.

### 5. Le digest consigné est celui de l'index

C'est la distinction que ce contrôle existe pour mesurer. L'index a son propre
digest, et c'est lui qu'on épingle : il désigne les deux architectures à la fois
et laisse le moteur du destinataire choisir la sienne. Le digest d'une des images
désigne **une** plateforme, et un déploiement épinglé dessus échoue partout
ailleurs.

Si vous consignez celui d'une image, le message vous le dira : c'est l'erreur
instructive, et la nommer vaut mieux qu'annoncer une différence.

## Le barème

Cinq contrôles de poids égal, seuil à **75 sur 100**, et **seul l'état final
compte**.

Quatre indices, du plus vague au plus explicite, et **ils coûtent des points** :

```bash
dsoxlab hint
```
