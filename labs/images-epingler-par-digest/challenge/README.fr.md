# Le même Dockerfile ne retrouve plus le même socle

## La situation

Le contexte `/opt/lab-image-pin/appli` construit une application sur
`127.0.0.1:15004/socle:stable`. Le registre a déplacé ce tag vers un socle que
personne n'a approuvé. Le fichier `/opt/lab-image-pin/approbation.json` donne la
référence et l'identité du socle approuvé.

## Mission

Sur `docker.lab`, corrigez `/opt/lab-image-pin/appli/Dockerfile` et construisez
`dsoxlab-pin:finale` depuis ce contexte.

### 1. La bonne livraison

`docker run --rm --network none dsoxlab-pin:finale` affiche l'identité du socle
approuvé, puis la source actuelle. L'image dérive des couches du socle approuvé.

### 2. Une nouvelle source entre dans le produit

Le contrôle copie votre contexte, change `source.txt` et reconstruit. Le produit
porte la nouvelle source et le socle approuvé.

### 3. Le socle ne suit pas le tag

Le contrôle déplace deux fois `stable` et reconstruit avec
`docker build --pull --no-cache`. Les couches du socle restent celles du socle
approuvé. Le tag est ensuite remis en place.

### Ce qui est interdit

Ne modifiez ni les socles, ni `approbation.json`, ni le registre. Une ancienne
image renommée ou une réponse écrite en dur ne passe pas. Le registre est en
HTTP et n'écoute que sur la boucle locale.
