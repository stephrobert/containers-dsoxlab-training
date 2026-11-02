# Épreuve : relier deux conteneurs

Deux conteneurs tournent sur cette machine. `vitrine` est la page que voient les
clients, `inventaire` est le service qui détient les articles.

## Ce qui est constaté

C'est tout ce qui est constaté, et aucun des trois constats ne dit la cause.

1. La vitrine répond, mais elle annonce que l'article est **injoignable**.
2. L'inventaire répond **depuis le réseau de l'entreprise**.
3. La vitrine répond elle aussi depuis le réseau de l'entreprise, alors qu'elle
   ne doit l'être que depuis cette machine.

## Les cinq contrôles

Ils sont de poids égal, et chacun porte sur un fait vérifiable.

### 1. Le nom `stock` se résout depuis la vitrine

Et il se résout vers une adresse que l'inventaire porte **réellement**. Un nom
qui pointe ailleurs est pire qu'un nom qui ne résout pas : la vitrine parlerait
à autre chose.

### 2. La requête traverse la vitrine puis l'inventaire

Mesuré **depuis cette machine**, sur `127.0.0.1:18311`. La réponse doit porter
la valeur que **seul l'inventaire** détient. Résoudre n'est pas joindre, et
joindre n'est pas obtenir une réponse : ce contrôle est le seul qui prouve la
chaîne entière.

### 3. La vitrine ne publie que sur l'interface demandée

**Un seul** port publié, et lié à **`127.0.0.1`** uniquement. Une adresse vide
ou `0.0.0.0` désigne toutes les interfaces de l'hôte, donc le réseau de
l'entreprise aussi.

### 4. L'inventaire ne publie aucun port, et quitte le réseau par défaut

**C'est l'exigence critique : elle n'est compensée par aucun total.** Une base
n'a aucune raison d'être joignable depuis l'extérieur, et sur le réseau par
défaut un conteneur a une adresse mais aucun nom, ce qui est la cause du
premier symptôme.

### 5. Le nom réel `inventaire` se résout aussi

L'exploitation continue de désigner le conteneur par son nom, celui des journaux
et des inventaires. Un nom supplémentaire **s'ajoute**, il ne remplace pas :
cette exigence écarte la correction par renommage.

## Ce qui est fourni

L'image `lab-relier:1.0` porte le service dans ses deux rôles. Rien à écrire,
rien à reconstruire. Elle attend deux variables d'environnement :

- `ROLE`, qui vaut `base` ou `vitrine` ;
- `CIBLE`, le nom que la vitrine interroge, soit `stock`.

Les deux conteneurs gardent leurs noms : les contrôles les cherchent nommément.

Ni volume ni Compose : ce n'est pas le sujet.

## Le barème

Cinq contrôles de poids égal, seuil à **75 sur 100**, et **seul l'état final
compte** : deux façons d'arriver au même état reçoivent la même note. Le nom que
vous donnez au réseau vous appartient.

Quatre indices, du plus vague au plus explicite, et **ils coûtent des points** :

```bash
dsoxlab hint
```
