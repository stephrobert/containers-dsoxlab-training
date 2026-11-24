# Les raccordements réseau forment une frontière mesurable

Le setup construit trois services HTTP depuis Alpine épinglée avec `busybox-extras`.
Les tests inspectent les raccordements réels aux bridges, leur caractère interne
et les publications de ports. Un essai avec données aléatoires prouve le chemin
complet façade vers API vers données.

L'isolation est testée avec un serveur sain : l'API accède aux données, tandis que
la façade échoue par nom DNS et IP directe. L'essai est répété après recréation
de tous les conteneurs pour refuser une modification réseau manuelle transitoire.
Le nettoyage retire uniquement les ressources du projet et les images étiquetées du lab.
