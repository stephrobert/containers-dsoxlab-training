# Remettre la stack en service

Une petite application tournait sur cette machine, en deux services Compose.
Sa composition a été perdue : les images sont là, les données de départ aussi,
et il n'y a plus rien qui les relie.

L'image locale `dsoxlab-epreuve-remettre-une-stack-en-service:service` porte
les deux rôles, et il n'y a **rien à écrire ni à reconstruire** :

- `donnees` sert son répertoire `/data` sur le port 8080, **sans rien
  publier** ;
- `frontal` va chercher la valeur chez un amont qu'il interroge **par le nom
  que la variable `CIBLE` lui donne**, puis la sert à son tour sur 8080.

Le frontal réessaie son amont pendant une minute avant d'abandonner : l'ordre
de démarrage ne vous posera donc aucun problème.

## Mission

Écrivez `/opt/lab-epreuve-remettre-une-stack-en-service/compose.yaml`, et
démarrez-la dans le projet
`dsoxlab-epreuve-remettre-une-stack-en-service`.

Ce qui est attendu à la fin :

- le projet porte **exactement** les deux services, `donnees` et `frontal`, et
  les deux tournent ;
- le frontal joint les données **par leur nom de service** : la façade rend la
  valeur que détient `donnees` ;
- **seul le frontal publie** un port, et seulement à l'adresse et sur le port
  que le fichier d'environnement fourni déclare ;
- une **donnée écrite avant une recréation est servie après** ;
- la composition **lit** l'adresse et le port dans
  `/opt/lab-epreuve-remettre-une-stack-en-service/.env` au lieu de les
  recopier, et sa forme résolue ne porte aucune variable en suspens.

## Ce que vous n'avez pas à faire

Ni sonde de santé, ni condition de dépendance : le frontal réessaie, et cela
suffit. Ni registre, ni image à construire, ni secret.

## Comment vous êtes noté

Cinq contrôles de poids égal, et **seul l'état final compte**. Aucune commande
n'est imposée, et les noms que vous donnez au réseau et au volume vous
appartiennent.

Le seuil est de **75 sur 100**. Une exigence ne se compense par aucun total :
**une donnée écrite avant une recréation et perdue après** fait échouer
l'épreuve, même avec tout le reste en place. C'est la seule chose qu'une
composition perd pour de bon.

Quatre indices sont disponibles, et **ils coûtent des points** : `dsoxlab hint`.
