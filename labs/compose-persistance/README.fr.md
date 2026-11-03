# Prouver la persistance par de nouvelles écritures

L'image fournie initialise seulement les données absentes. Trois contrôles
mesurent le montage nommé, la recréation forcée et down/up sans suppression du volume.
Les écritures aléatoires distinguent la persistance d'une simple copie répétée
de la donnée initiale. Les tests restaurent le contenu original ; le nettoyage
supprime uniquement les ressources du projet et son image étiquetée.
Aucun redémarrage de l'hôte n'est demandé ni attesté.

Chaque essai mesure aussi l'UID non-root et les permissions avant et après
remplacement. Un volume conserve son propriétaire ; il n'accorde pas
automatiquement l'accès à un nouvel UID. Préparez les droits une fois et gardez
le répertoire privé. Cela protège les identités applicatives, pas les
utilisateurs qui contrôlent le socket Docker.

Ce lab n'exige **pas** de racine en lecture seule : elle s'enseigne bien plus
loin dans le parcours, et une exigence qu'aucune leçon n'a encore présentée
n'entraîne pas, elle bloque.
