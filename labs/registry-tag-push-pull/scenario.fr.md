# Construite ici, disponible ailleurs

Sur `docker.lab`, l'image `dsoxlab-registry-app:release` affiche la release du
jour. Elle existe uniquement dans le moteur local. Le registre
`127.0.0.1:15000` est vide.

L'atelier est dans `/opt/lab-registry-push/appli`. L'image et son produit sont
déjà construits : votre travail est de les distribuer, pas de les remplacer.

## Mission

- Nommez cette image `127.0.0.1:15000/catalogue/appli:1.0`.
- Publiez-la dans le registre.
- Retrouvez-la depuis le registre et vérifiez son résultat avec `docker run`.
- Un client sans accès au cache de votre moteur doit pouvoir récupérer toutes
  ses couches et exécuter la même release sans réseau.

Ne modifiez ni le registre ni la référence conservée par le banc. Le registre
HTTP est limité à la boucle locale : aucun accès non chiffré à un registre
externe n'est nécessaire, et aucune modification du démon n'est attendue.

Un `docker run` local ne prouve pas le push : le moteur peut déjà avoir l'image.
Les contrôles lisent le manifeste distant, téléchargent une archive avec Skopeo
sans consulter le cache Docker, puis chargent et exécutent cette archive.
Ils ne suppriment jamais votre release pour simuler un client vierge.
