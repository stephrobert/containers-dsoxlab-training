# Trois environnements, une déclaration confuse

Dans `/opt/lab-compose-vars`, aucun conteneur ne tourne. La déclaration fournie
confond interpolation par Compose et développement par le shell du conteneur.

- `deploy.env` fournit `IMAGE_REF` et la valeur approuvée de `APP_RELEASE` ;
- `.env` contient des valeurs implicites trompeuses ;
- `runtime.env` fournit `RUNTIME_ONLY` et un ancien `APP_MODE=staging`.

## Mission

Réparez seulement `compose.yaml` ; gardez les trois fichiers d'environnement inchangés.
Démarrez exactement un service nommé `app` dans le projet `dsoxlab-resolution-variables`.

Utilisez `--env-file /opt/lab-compose-vars/deploy.env` pour l'interpolation :
l'image doit provenir de `IMAGE_REF` et la variable `APP_RELEASE` du conteneur
doit provenir de l'interpolation de `APP_RELEASE`, pas d'une copie littérale.
Utilisez `env_file` au niveau du service pour injecter `runtime.env`, puis
surchargez `APP_MODE` à `production` avec `environment`.

Au démarrage, le shell du conteneur doit écrire `/tmp/report` contenant exactement :

```text
production:<APP_RELEASE résolue>:<RUNTIME_ONLY depuis runtime.env>
```

Gardez le conteneur démarré. Utilisez l'image épinglée fournie, sans construction,
montages de remplacement ni modifications manuelles dans les conteneurs.
Échappez les dollars destinés au conteneur pour éviter leur développement par Compose.

Inspectez à la fois `docker compose ... config` et l'environnement réel du conteneur.
Un fichier d'interpolation n'injecte pas automatiquement toutes ses valeurs dans un conteneur.
Le contrôle recrée le service avec une nouvelle `APP_RELEASE` issue du shell,
qui doit primer sur `deploy.env`, puis recrée le déploiement original.
Ne dépendez ni du `.env` implicite ni d'une variable exportée dans votre session.
