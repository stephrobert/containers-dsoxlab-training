# Interpolation Compose et environnement du conteneur

Le setup fournit une déclaration fautive, un environnement explicite de déploiement,
des valeurs implicites trompeuses et un environnement runtime séparé. Aucun conteneur
n'existe initialement.

Trois contrôles mesurent la configuration résolue, l'environnement réel et le rapport
au démarrage, puis forcent une recréation avec surcharge aléatoire du shell.
Le déploiement original est restauré dans `finally`. Les empreintes du setup
protègent les fichiers d'environnement fournis. Le nettoyage retire uniquement
les ressources étiquetées de ce projet Compose et ses fichiers de lab.
L'image de base épinglée est conservée ; aucune image applicative n'est construite.
