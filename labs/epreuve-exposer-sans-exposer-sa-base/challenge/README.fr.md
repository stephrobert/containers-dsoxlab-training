# La vitrine ne joint plus son inventaire, et la base sort trop

Un petit magasin en ligne tourne sur cette machine, en deux conteneurs.
`vitrine` est la page que voient les clients, `inventaire` est le service qui
détient les articles. Les deux ont été lancés à la main, dans l'urgence, et
depuis ce jour trois choses sont remontées.

**Le premier constat vient des clients.** La vitrine répond, mais elle annonce
que l'article est injoignable. Elle n'est pas en panne : elle n'obtient rien de
l'inventaire.

**Le deuxième vient de l'audit interne.** L'inventaire répond depuis le réseau
de l'entreprise. Une base de données n'a aucune raison d'y être joignable.

**Le troisième vient du même audit.** La vitrine aussi répond depuis le réseau
de l'entreprise, alors qu'elle ne doit l'être que depuis cette machine : un
relais la publiera plus tard, et c'est lui qui portera la façade.

**Le quatrième est le plus discret.** L'inventaire sort vers l'extérieur. Une
base de données n'a aucune raison de le faire, et c'est ce qui transforme une
lecture non autorisée en fuite : sans issue, la donnée reste là où elle est,
même quand le service est compromis.

Aucun des quatre constats ne dit la cause. C'est à vous de l'établir.

## Ce qui est attendu à la fin

- la vitrine est joignable sur le port **18311**, **depuis cette machine
  seulement** ;
- l'inventaire répond au nom **`stock`**, qui est écrit dans la configuration
  de la vitrine et ne se change pas. C'est le nom d'un **service**, pas celui
  d'un conteneur : renommer l'inventaire ne convient donc pas ;
- l'inventaire est sur un réseau **sans issue**, et ne peut plus sortir ;
- l'inventaire **ne publie plus aucun port** ;
- et la requête métier **aboutit quand même**, de bout en bout.

Les deux conteneurs gardent leurs noms, `vitrine` et `inventaire` : les
contrôles les cherchent nommément.

## Ce que vous n'avez pas à écrire

L'image `lab-relier:1.0` porte le service, dans ses deux rôles. Il n'y a aucun
code à écrire ni à reconstruire : elle attend deux variables d'environnement,
`ROLE`, qui vaut `base` ou `vitrine`, et `CIBLE`, le nom que la vitrine
interroge. L'énoncé complet est aussi sur la machine, dans
`/opt/lab-relier/MISSION.md`.

Ni volume ni Compose : ce n'est pas le sujet de cette épreuve.

## Comment vous êtes noté

Cinq contrôles de poids égal, et **seul l'état final compte**. Deux façons
d'arriver au même état reçoivent la même note : aucune commande n'est imposée,
et le nom que vous donnez au réseau vous appartient.

Le seuil est de **75 sur 100**. Une exigence ne se compense par aucun total :
**un port publié sur l'inventaire** fait échouer l'épreuve, même avec tout le
reste en place. C'est le défaut que l'audit a relevé, et c'est celui qui expose
une base de données à toute l'entreprise.

Quatre indices sont disponibles, et **ils coûtent des points** : `dsoxlab hint`.

## Épreuve : exposer une application sans exposer sa base

Deux conteneurs tournent sur cette machine. `vitrine` est la page que voient les
clients, `inventaire` est le service qui détient les articles.

### Ce qui est constaté

C'est tout ce qui est constaté, et aucun des quatre constats ne dit la cause.

1. La vitrine répond, mais elle annonce que l'article est **injoignable**.
2. L'inventaire répond **depuis le réseau de l'entreprise**.
3. La vitrine répond elle aussi depuis le réseau de l'entreprise, alors qu'elle
   ne doit l'être que depuis cette machine.
4. L'inventaire **sort vers l'extérieur**. Une base de données n'a aucune
   raison de le faire, et c'est ce qui transforme une lecture non autorisée en
   fuite.

### Les cinq contrôles

Ils sont de poids égal, et chacun porte sur un fait vérifiable.

#### 1. La vitrine ne publie que sur l'interface demandée

**Un seul** port publié, et lié à **`127.0.0.1`** uniquement. Une adresse vide
ou `0.0.0.0` désigne toutes les interfaces de l'hôte, donc le réseau de
l'entreprise aussi.

#### 2. L'inventaire répond à `stock`, qui n'est pas son nom

`stock` est écrit dans la configuration de la vitrine et **ne se change pas**.
Ce contrôle ne regarde pas seulement la résolution : il lit le **nom de service
déclaré**. Un conteneur qu'on renommerait `stock` résoudrait aussi, et lierait
la vitrine à un conteneur précis au lieu d'un service.

#### 3. L'inventaire est sur un réseau **sans issue**

Deux faits, et le second est celui qui prouve. Tous les réseaux de l'inventaire
sont déclarés **internes**, et surtout l'inventaire **n'a aucune route par
défaut**, ce qui se lit dans le conteneur. La déclaration est une intention ;
l'absence de route est l'effet.

#### 4. L'inventaire ne publie aucun port

**C'est l'exigence critique : elle n'est compensée par aucun total.** Une base
n'a aucune raison d'être joignable depuis l'extérieur : sa vitrine l'atteint
par le réseau des conteneurs. Rien ne retire un port publié sur un conteneur
qui existe déjà, ce qui est en soi une information.

#### 5. La requête métier aboutit **malgré** l'isolement

Mesuré **depuis cette machine**, sur `127.0.0.1:18311`. La réponse doit porter
la valeur que **seul l'inventaire** détient.

C'est pour ce contrôle que l'épreuve existe : isoler la base la coupe de tout,
publier la vitrine demande au contraire une issue, et les deux doivent tenir
ensemble. Chacune des exigences se règle facilement seule.

### Ce qui est fourni

L'image `lab-relier:1.0` porte le service dans ses deux rôles. Rien à écrire,
rien à reconstruire. Elle attend deux variables d'environnement :

- `ROLE`, qui vaut `base` ou `vitrine` ;
- `CIBLE`, le nom que la vitrine interroge, soit `stock`.

Les deux conteneurs gardent leurs noms : les contrôles les cherchent nommément.

Ni volume ni Compose : ce n'est pas le sujet.

### Le barème

Cinq contrôles de poids égal, seuil à **75 sur 100**, et **seul l'état final
compte** : deux façons d'arriver au même état reçoivent la même note. Le nom que
vous donnez au réseau vous appartient.

Quatre indices, du plus vague au plus explicite, et **ils coûtent des points** :

```bash
dsoxlab hint
```
