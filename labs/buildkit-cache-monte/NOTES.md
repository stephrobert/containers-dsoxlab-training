# Un cache qui survit à l'étape, pas dans l'image

Le lab distingue cache des couches et montage de cache : la source change,
l'étape rejoue et sa dépendance reste réutilisable hors de l'image.

Mesuré sur `docker.lab` le 2026-11-01, avec le BuildKit épinglé du scénario :
un changement d'argument de build donne `miss` puis `hit`, avec un nouveau
produit ; `/cache/dependency` est absent de l'image. En revanche, deux builds
avec `--no-cache` donnent `miss` puis `miss`. Les tests changent donc la source,
pas cette option.

Le dépôt de dépendances est local et l'installation volontairement petite :
aucun seuil temporel ne confond qualité du cache et débit internet. Le cache
vide doit fonctionner ; le cache rempli doit éviter la réinstallation.

Trois contrôles : produit à froid et à chaud, réutilisation après changement
de source et absence du cache dans l'image. Le premier exige aussi que la
réutilisation soit rétablie, pour ne pas donner des points sur l'état initial.
Chaque notation crée puis retire son propre constructeur et son volume de
cache, sans purger les caches des autres labs.
