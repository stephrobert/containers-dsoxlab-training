# Remettre la stack en service

L'image locale `dsoxlab-compose-capstone:service` contient deux rôles.
`writer` copie un marqueur release fourni dans `/data` puis s'arrête ; `web`
sert ce fichier sur le port 8080. Aucun conteneur applicatif ni volume n'existe.

## Mission

Créez `/opt/lab-compose-capstone/compose.yaml` pour le projet
`dsoxlab-compose-capstone`. Déclarez exactement deux services avec l'image
fournie : `writer` avec `ROLE=writer` et `web` avec `ROLE=web`. Utilisez un
volume nommé monté sur `/data` par les deux services. `writer` doit réussir
avant web, qui monte les données en lecture seule.

Gardez web sain et publiez `8080` uniquement sur `127.0.0.1:18092`. Démarrez
la stack en arrière-plan. Le point d'accès `/release.txt` doit renvoyer le
marqueur release fourni. La recréation de web seul ne doit ni recréer writer ni
perdre les données. Les tests effectuent cette recréation limitée et laissent
la stack démarrée.
