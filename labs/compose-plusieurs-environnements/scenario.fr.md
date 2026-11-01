# Une application, deux déploiements indépendants

`/opt/lab-compose-env/compose.yaml` fournit un service `app` de base avec volume
nommé et réglages provisoires d'environnement/mémoire. Gardez cette base inchangée.
L'image fournie sert `APP_ENV` sur `/environment.txt` au port 8080 et initialise
`/data/value.txt` seulement s'il manque. Aucun déploiement ne tourne initialement.

## Mission

Écrivez `dev.yaml` et `prod.yaml` dans le même dossier. Fusionnez la base d'abord,
puis la surcharge choisie avec deux options `-f`. Exécutez simultanément les projets :

| Surcharge | Projet | APP_ENV | Mémoire | Publication |
|---|---|---|---|---|
| dev.yaml | dsoxlab-env-dev | development | 64 Mio | 127.0.0.1:18090:8080 |
| prod.yaml | dsoxlab-env-prod | production | 128 Mio | 127.0.0.1:18091:8080 |

Chaque projet doit avoir exactement une app, son volume nommé et son réseau.
Gardez image/commande et montage hérité, sans montages de remplacement, noms globaux
ni ressources externes partagées.

Les deux points HTTP doivent servir leur environnement réel. Recréer un projet
doit préserver ses nouvelles données et laisser inchangées l'identité du conteneur
et les données de l'autre. Aucune copie manuelle, construction ni téléchargement
n'est nécessaire. Les contrôles recréent indépendamment les projets avec données
aléatoires puis restaurent le contenu original.
