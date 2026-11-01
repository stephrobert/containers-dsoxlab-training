# Une CI qui teste réellement l'application

Travaillez sur `docker.lab` dans `/opt/lab-compose-ci`. Source, Dockerfile,
stack Compose et test d'intégration sont fournis ; `ci.sh` refuse actuellement
de démarrer. Aucun compte de CI hébergée n'est nécessaire.

Implémentez un `ci.sh` POSIX exécutable. Son contrat d'environnement :
`PROJECT` (projet Compose unique), `SOURCE_DIR` (contexte absolu),
`ARTIFACT_DIR` (répertoire de rapports existant), `EXPECTED_VALUE`, `TEST_FAIL`
(0 normalement, 1 force un vrai échec du test). Gardez le fichier Compose et
le test fournis sans remplacer leur logique. Exemple manuel :

```sh
cd /opt/lab-compose-ci
mkdir -p artifacts
PROJECT=dsoxlab-ci-manual SOURCE_DIR="$PWD/source" ARTIFACT_DIR="$PWD/artifacts" \
EXPECTED_VALUE=release-one TEST_FAIL=0 ./ci.sh
```

Chaque exécution construit la source indiquée, démarre seulement l'API,
attend sa santé, exécute le conteneur de tests, conserve `result.json`, retourne
le statut du test et retire conteneurs, réseaux et volumes de ce projet même
en échec. Modifier `value.txt` doit changer la livraison testée à l'exécution
suivante. Aucun port hôte, prune global ni suppression des images de base.
Conservez les labels de propriété.

L'évaluation exécute de vrais jobs, force l'échec et modifie la source ; du
YAML valide ou un rapport de succès écrit à la main ne rapporte rien.
Le setup utilise le réseau pour apt et la base Python épinglée. Ensuite les
jobs n'ont besoin d'aucun téléchargement ni réseau sortant. Compose v2 avec
`up --wait` et BuildKit sont requis.
