# Le produit est privé, pas le secret dans l'image

Sur `docker.lab`, `/opt/lab-buildkit-secret/appli` contient un Dockerfile qui
récupère un produit dans un dépôt privé. Le dépôt répond sur l'adresse de la VM,
port `18083`, chemin `/artifact`, et exige `Authorization: Bearer <secret>`.
Le secret pédagogique est dans `/opt/lab-buildkit-secret/depot.token`, hors du
contexte de build.

Le Dockerfile de départ passe le secret par `ARG DEPOT_SECRET`. Le conteneur
ne le conserve pas dans son environnement, mais l'historique de l'image le révèle.
Le copier puis le supprimer ne résout pas le problème : les couches précédentes
restent distribuées avec l'image.

## Mission

Corrigez le Dockerfile et construisez `dsoxlab-secret:finale`.

- Le conteneur affiche uniquement le produit privé dans `/produit.txt`.
- Aucun secret n'apparaît dans la configuration, l'historique ou les couches.
- Une nouvelle identité passée par `--secret id=depot,src=...` permet de reconstruire.
- Un secret absent ou erroné fait échouer un build exécuté sans cache des couches.
- Le fichier d'identifiant ne séjourne pas dans le répertoire de contexte.

Le dépôt et son état sont le banc de mesure : ne les modifiez pas. Le protocole
HTTP est ici réservé au réseau isolé du lab ; le TLS du dépôt n'est pas le sujet.

Vous pouvez préparer le constructeur ainsi :

```bash
docker buildx create --name dsoxlab-secret-work --driver docker-container \
  --driver-opt image=moby/buildkit@sha256:99368f3e46177c6405b9740e4461d91cee004128daeecca78d4ceac50ec1da5c
```

Passez `DEPOT_URL=http://<adresse-de-docker.lab>:18083/artifact` comme argument
de build et le fichier d'identifiant comme secret BuildKit. Ce n'est pas un
argument `DEPOT_SECRET`, et il ne doit pas être copié dans le contexte : les
contrôles vérifient que le répertoire `appli` ne le contient pas, même exclu
par un `.dockerignore`.

Un constructeur `docker-container` ne dépose pas l'image dans le magasin local :
il la garde dans son propre cache. Sans `--load`, la construction réussit, puis
`docker run` répond « Unable to find image ... locally » suivi d'un
« may require 'docker login' » qui n'a rien à voir avec votre problème.
Construisez donc avec `--load`, les contrôles lisant l'image depuis le magasin
local.

Les contrôles lisent votre image, puis reconstruisent une copie du contexte
avec un produit et une identité neufs. Ils restaurent le dépôt après les essais.
Le nettoyage retire uniquement le service, les fichiers et les constructeurs
nommés de ce lab.
