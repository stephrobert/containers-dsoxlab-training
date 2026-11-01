# Migration ponctuelle sur une vraie base SQLite

Trois contrôles mesurent la migration et sa dépendance, les rejeux idempotents avec
données nouvelles et les démarrages à froid ou en échec dans des projets jetables.
Le refus de démarrage exige que app reste créée, pas qu'elle démarre puis plante.
Les volumes d'essai sont retirés ; la base apprenante reste jusqu'au nettoyage.
SQLite est installé lors de la construction de l'image de banc depuis Alpine épinglée.
