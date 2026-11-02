# La vitrine ne joint plus son inventaire

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

Aucun des trois constats ne dit la cause. C'est à vous de l'établir.

## Ce qui est attendu à la fin

- la vitrine joint l'inventaire par le nom **`stock`**, qui est écrit dans sa
  configuration et ne se change pas ;
- l'exploitation continue de désigner l'inventaire par son nom réel,
  **`inventaire`** : les deux noms doivent résoudre ;
- la vitrine est joignable sur le port **18311**, **depuis cette machine
  seulement** ;
- l'inventaire **ne publie plus aucun port**.

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
