# Chaque changement de source réinstalle les dépendances

Sur `docker.lab`, le contexte `/opt/lab-buildkit-cache` fabrique un produit à
partir de `source/version.txt` et d'une dépendance du dépôt local `depot/`.
L'outil `fabriquer.sh` installe la dépendance dans `/cache`, puis écrit le produit
et un reçu sous `/produit`. Le dépôt local rend l'exercice indépendant du débit
d'internet ; il représente ici la dépendance récupérée par le gestionnaire de
paquets.

Le Dockerfile fonctionne, mais chaque changement de source réinstalle la même
dépendance. Son cache finit aussi dans l'image d'exécution.

## Mission

Corrigez le Dockerfile, sans modifier l'outil, pour que :

- un constructeur neuf réussisse avec un cache vide ;
- deux versions différentes de la source produisent chacune leur propre produit ;
- le deuxième build réutilise la dépendance, même si l'étape de fabrication rejoue ;
- `/cache` ne porte aucune dépendance dans l'image d'exécution.

Le reçu indique `cache=miss` ou `cache=hit`, la source, l'empreinte de fabrication
et le SHA-256 de la dépendance. Le contenu de `/produit/dependency.txt` doit rester
celui du dépôt.

Vous pouvez créer un constructeur dédié nommé `dsoxlab-cache-work` :

```bash
docker buildx create --name dsoxlab-cache-work --driver docker-container \
  --driver-opt image=moby/buildkit@sha256:cec9f139f45e93c5c69c60f8b07cfad9f43f4ef6b6a6cd917527fea5ff2e3dea
docker buildx build --builder dsoxlab-cache-work --load \
  -t dsoxlab-cache:finale /opt/lab-buildkit-cache
docker run --rm dsoxlab-cache:finale
```

Changez la source pour invalider l'étape : un simple deuxième build identique
ne prouve que le cache des couches. Ne forcez pas `--no-cache` : sur la version
BuildKit de ce banc, cette option remet aussi le montage de cache à vide.

Les contrôles utilisent un constructeur isolé, changent la source puis la
restaurent. Ils jugent des produits reconstruits, pas le temps écoulé ni les
commandes tapées. `clean` retire uniquement les objets nommés de ce lab.
