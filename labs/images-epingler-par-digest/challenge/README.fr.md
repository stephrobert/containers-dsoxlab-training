# Le même Dockerfile ne retrouve plus le même socle

Sur `docker.lab`, le contexte `/opt/lab-image-pin/appli` construit une application
sur `127.0.0.1:15004/socle:stable`. Le registre a déplacé ce tag vers un socle
non approuvé. Le bon `/opt/lab-image-pin/approbation.json` donne le digest de
manifeste du socle approuvé et son identité.

Le lab précédent retrouvait un conteneur par digest. Ici, c'est une
**reconstruction future** qui doit garder le bon socle, tout en intégrant une
source applicative nouvelle.

## Mission

- Corrigez le Dockerfile de l'application pour utiliser le socle approuvé.
- Construisez `dsoxlab-pin:finale` depuis ce contexte.
- Le conteneur doit afficher le socle approuvé puis la source courante :
  `docker run --rm --network none dsoxlab-pin:finale`.
- Changer la source doit changer le produit, sans changer les couches du socle.
- Un déplacement de `stable` ne doit pas changer le socle d'une reconstruction
  forcée avec `docker build --pull --no-cache`.

Ne modifiez pas les socles, le bon d'approbation ou le registre. Le constructeur
ne doit pas se contenter d'une vieille image finale ou d'une réponse écrite en dur.
Le registre HTTP écoute seulement en boucle locale.

Les contrôles copient votre contexte, changent sa source, déplacent deux fois
le tag `stable` et reconstruisent. Ils exécutent les produits sans réseau et
comparent les couches aux couches approuvées. Le tag est ensuite restauré.

## Mission : reconstruire sans changer de socle

Sur `docker.lab`, corrigez `/opt/lab-image-pin/appli/Dockerfile` et construisez
`dsoxlab-pin:finale` avec le digest du bon `/opt/lab-image-pin/approbation.json`.
Une nouvelle source doit être intégrée sans suivre les changements de `stable`.

Le scénario donne le banc et les critères.
