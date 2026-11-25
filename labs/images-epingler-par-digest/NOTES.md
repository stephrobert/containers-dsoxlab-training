# Épingler la dépendance d'une reconstruction

Le lab distingue le retour à une image existante et l'épinglage d'un `FROM`.
Deux socles locaux ont des couches et des identités différentes. Le tag
`stable` est déjà déplacé au départ, et aucune image finale n'est construite.

Les trois contrôles prouvent la livraison initiale, l'intégration d'une source
nouvelle et la stabilité des couches du socle malgré un tag déplacé.
Ils exigent d'abord une livraison correcte pour ne donner aucun point au départ.

Le changement de tag est réel dans le registre. Les builds utilisent `--pull`
et `--no-cache`, et les produits s'exécutent sans réseau : ni cache local,
ni résultat fixe, ni fichier du contexte qui imite le socle ne suffit.
Les tests restaurent le tag et retirent leur contexte et leurs images.
Le nettoyage est limité aux objets du lab, étiquetés par leur propriétaire.
