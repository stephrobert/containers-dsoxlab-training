# Stable n'a pas gardé la même image

Sur `docker.lab`, le registre `127.0.0.1:15002` a reçu deux releases sous
`catalogue/appli:stable`. Le tag pointe maintenant vers la seconde. Le conteneur
`dsoxlab-digest-app`, lancé par ce tag, exécute le mauvais produit.

Le bon de la première livraison est dans
`/opt/lab-registry-digest/livraison.json`. Il donne sa référence de registre
avec le digest du manifeste et le produit attendu. Le contexte `appli/`
contient désormais la deuxième release : reconstruire ce contexte ne retrouve
pas la première.

## Mission

- Récupérez l'image de la première livraison depuis le registre.
- Remplacez `dsoxlab-digest-app` par un conteneur actif de cette image.
- Lancez-le par la référence de registre avec son digest, et non par un tag
  recréé.
- `docker exec dsoxlab-digest-app cat /release.txt` doit rendre le produit
  original du bon de livraison.

Gardez le tag `stable` et le registre intacts. Le but est de retrouver un contenu
immuable malgré un tag déplacé, pas de réécrire l'histoire du registre.
Le registre HTTP n'écoute que sur la boucle locale.

Une précision mesurée sur ce moteur, parce qu'elle surprend : **l'identifiant
local de l'image et le digest poussé sont la même valeur**. Docker 29 sur le
magasin containerd publie un index OCI, et c'est le digest de cet index qui vaut
l'identifiant de l'image ; le manifeste servi n'a d'ailleurs aucune clé de
configuration. Il n'y a donc pas deux identités à distinguer.

Ce qui est contrôlé, c'est la **référence de démarrage**. Lancer par un tag
recréé donne le bon contenu et une référence qui mentira au prochain déplacement
du tag ; lancer par le digest donne une référence qui ne peut pas mentir.

Les contrôles vérifient l'image réellement exécutée, sa référence de démarrage,
son produit et la disponibilité du manifeste d'origine avec un client
indépendant.
