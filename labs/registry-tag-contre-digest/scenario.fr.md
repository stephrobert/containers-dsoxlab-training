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
- Lancez-le par la référence de registre avec son digest, pas par un tag
  recréé ni par son ID de configuration.
- `docker exec dsoxlab-digest-app cat /release.txt` doit rendre le produit
  original du bon de livraison.

Gardez le tag `stable` et le registre intacts. Le but est de retrouver un contenu
immuable malgré un tag déplacé, pas de réécrire l'histoire du registre.
Le registre HTTP n'écoute que sur la boucle locale.

Le digest du manifeste et l'ID de configuration sont deux identités distinctes.
Les contrôles vérifient l'image réellement exécutée, sa référence de démarrage,
son produit et la disponibilité du manifeste d'origine avec un client indépendant.
