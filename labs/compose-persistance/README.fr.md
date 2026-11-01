# Prouver la persistance par de nouvelles écritures

L'image fournie initialise seulement les données absentes. Trois contrôles
mesurent le montage nommé, la recréation forcée et down/up sans suppression du volume.
Les écritures aléatoires distinguent la persistance d'une simple copie répétée
de la donnée initiale. Les tests restaurent le contenu original ; le nettoyage
supprime uniquement les ressources du projet et son image étiquetée.
Aucun redémarrage de l'hôte n'est demandé ni attesté.
