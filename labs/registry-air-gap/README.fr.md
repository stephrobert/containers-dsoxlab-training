# Mesurer la livraison, pas le cache Docker local

Le produit est tiré et publié au setup ; son tag local est retiré.
Aucune livraison ni somme d'intégrité n'existe au départ.

Deux contrôles valident un reçu portable et une archive Docker complète, puis
récupèrent et exécutent le produit exact avec le registre d'origine arrêté.
Skopeo lit tous les blobs de l'archive dans un répertoire neuf avant
d'impliquer Docker : ses couches préexistantes ne peuvent donc pas masquer
des couches absentes de l'archive. L'essai hors ligne n'utilise que ce
répertoire, jamais une référence réseau.

Le registre d'origine est restauré dans un bloc finally ; le tag importé
d'essai et les répertoires temporaires sont retirés. Le nettoyage ne vise que
les objets nommés et les images étiquetées de ce lab. Les images Alpine et
Registry d'origine sont conservées. HTTP sur la boucle locale est un banc
d'emballage volontaire, pas une recommandation TLS.
