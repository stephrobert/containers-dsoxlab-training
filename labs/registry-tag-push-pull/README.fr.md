# Le cache local ne prouve pas une publication

Ce lab distribue une image déjà construite vers un registre local vide.
Un produit tiré au setup distingue la release d'une réponse fixe.

Le premier contrôle lit le manifeste du registre et compare son identité à
la référence. Le second récupère toutes les couches avec Skopeo dans une archive
neuve, charge cette archive et exécute l'image sans réseau.

Mesuré le 2026-11-01 sur `docker.lab` : une image poussée vers le registre
Distribution épinglé est récupérable par Skopeo, rechargeable par Docker et
exécutable sans accès à un registre. Ce transfert ne consulte pas le cache
Docker du producteur, même si les deux outils sont sur la même VM.

Le registre écoute uniquement en boucle locale. Les tests retirent leur archive,
leur conteneur et leur étiquette ; le cleanup retire le registre et son stockage,
sans purger les objets des autres labs.
