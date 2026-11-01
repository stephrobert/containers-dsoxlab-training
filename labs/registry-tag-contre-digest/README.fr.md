# Un tag se déplace, son ancien digest reste adressable

Le setup publie deux produits aléatoires sous le même tag et lance le second.
Il conserve le digest du manifeste original dans un bon de livraison.

Trois contrôles prouvent que l'image d'origine est en service, que sa référence
de démarrage est immuable et que le manifeste reste lisible dans le registre.
Chaque contrôle exige d'abord le retour du produit d'origine : aucune note
ne récompense l'état de départ.

Le registre est propre au lab et n'écoute qu'en boucle locale. Le nettoyage
retire ses conteneurs, ses références et son stockage, sans purge globale.

Cycle mesuré sur `docker.lab` le 2026-11-01 : 0/3 avant, 3/3 après,
0/3 après `clean` et `run`, puis moteur rendu intact. Le contrôle du registre
vérifie aussi que `stable` pointe toujours vers le produit de remplacement.
