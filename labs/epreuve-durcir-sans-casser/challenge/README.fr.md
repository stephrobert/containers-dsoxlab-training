# Épreuve : durcir sans casser

Le service tourne avec tous les droits par défaut, son secret est dans son
environnement, sa racine est inscriptible, et il ne joint plus son fournisseur.

## Les cinq contrôles

Ils sont de poids égal, et chacun porte sur un fait vérifiable.

### 1. Les droits retirés, et le service qui répond encore

**Trois faits** : le jeu de capabilities est réduit, `no-new-privileges` est
posé, et le service répond. Le troisième distingue cette épreuve d'un exercice de
suppression : tout retirer est facile, et le service meurt.

Le contrôle **n'impose aucune capability par son nom**. Il mesure que le jeu est
réduit et que le service tourne : un apprenant qui trouve un autre chemin pour se
passer de la capability a mieux durci, et l'épreuve ne doit pas le punir.

### 2. La racine en lecture seule, et les écritures déclarées

Deux faits qui n'ont de sens qu'ensemble : une racine en lecture seule sans
chemin d'écriture déclaré donne un service qui meurt, et un chemin déclaré sans
racine en lecture seule ne protège rien.

Le contrôle les mesure **en faisant** : une écriture hors des chemins déclarés
doit être refusée. Lire `ReadonlyRootfs` ne suffirait pas, car le drapeau dit
l'intention et l'essai dit le résultat.

### 3. Le secret hors de l'environnement, et pourtant arrivé

**Première exigence critique.** Deux faces : le secret a disparu de
l'environnement et de l'image, **et** le service le reçoit. Retirer une variable
sans la remplacer donne un service propre et faux, et le contrôle compare la
valeur servie à celle qu'il attend.

### 4. Le flux rétabli, le pare-feu intact

**Seconde exigence critique**, et la fausse correction la plus tentante de
l'épreuve : retirer le pare-feu fait disparaître le symptôme en une commande et
laisse la machine nue.

Trois faits mesurés ensemble : le flux aboutit, la table existe toujours, et la
protection **protège encore**. Le troisième est le plus fin : une correction qui
vide la chaîne lève le blocage **et** la protection, ce qui ressemble à un travail
fait. Le contrôle ne se contente donc pas de lire la règle, il vérifie qu'elle
agit.

### 5. Le volume utile servi, les jetables retirés

Le durcissement passe par une recréation du conteneur, et c'est là qu'un volume
s'oublie. Trois volumes portent le nom du lab : un seul compte, et l'énoncé dit
lequel.

Le contrôle lit **la donnée servie**, et non la seule existence du volume : un
volume remonté vide porte le bon nom et ne vaut rien.

## Le barème

Cinq contrôles de poids égal, seuil à **75 sur 100**, et **deux** exigences
critiques.

Quatre indices, du plus vague au plus explicite, et **ils coûtent des points** :

```bash
dsoxlab hint
```
