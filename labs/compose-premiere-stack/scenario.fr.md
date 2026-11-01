# Deux images ne font pas encore une application

Sur `docker.lab`, deux images sont préparées, mais aucun service ne tourne :

- `dsoxlab-compose-first:api` sert `/release.txt` sur le port `8080` ;
- `dsoxlab-compose-first:web` sert `/cgi-bin/release` sur le port `8080` et
  récupère le contenu actuel de l'API par `http://api:8080/release.txt`.

Web a donc besoin de découverte de services, pas d'une IP de conteneur figée.
Aucune image publique n'est à télécharger ; les deux images ont été construites
depuis Alpine épinglée.

## Mission

Écrivez `/opt/lab-compose-first/compose.yaml` et démarrez-le sous le nom de
projet Compose `dsoxlab-premiere-stack` :

- exactement deux services démarrés, `api` et `web`, avec les images fournies ;
- un réseau dédié commun où `api` se résout par son nom de service ;
- le port `8080` de web publié seulement sur `127.0.0.1:18086` ;
- aucun port de l'API publié sur l'hôte ;
- `http://127.0.0.1:18086/cgi-bin/release` relaie la release actuelle de l'API.

La déclaration doit recréer les deux services par une seule invocation Compose,
sans préparation manuelle de conteneurs, build ou pull. Gardez les commandes et
le contenu des images fournis ; ne montez pas de fichiers applicatifs de
remplacement. Utilisez le même nom de projet à chaque invocation pour que
Compose gère une seule application.

Le contrôle change brièvement le contenu de l'API et exige que web le relaie,
puis le restaure. Il recrée aussi les deux conteneurs depuis votre déclaration.
Ne comptez pas sur des modifications manuelles éphémères dans les conteneurs.

```bash
docker compose -p dsoxlab-premiere-stack \
  -f /opt/lab-compose-first/compose.yaml ps
```
