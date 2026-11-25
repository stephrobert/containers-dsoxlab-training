# Fusionner une base, isoler par projet

Trois contrôles mesurent réglages fusionnés et identité HTTP réelle, puis remplacent
chaque environnement sur sa VM distincte avec des données persistantes nouvelles.
Le setup construit une fois puis transfère l'archive inchangée à la seconde VM.
Les identifiants des deux images exécutées doivent correspondre au digest
protégé de l'image préparée ; aucun build Compose de déploiement n'est autorisé.
L'empreinte de la base refuse les modifications de configuration commune.
Les tests restaurent les données ; le nettoyage retire seulement les deux projets
du lab et l'image étiquetée. La construction installe busybox-extras.
