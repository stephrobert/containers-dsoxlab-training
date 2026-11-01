# Une application, deux déploiements indépendants

`/opt/lab-compose-env/compose.yaml` fournit un service `app` de base avec volume
nommé et réglages provisoires d'environnement/mémoire. Gardez cette base inchangée.
L'image fournie sert `APP_ENV` sur `/environment.txt` au port 8080 et initialise
`/data/value.txt` seulement s'il manque. Aucun déploiement ne tourne initialement.

## Mission

Écrivez `dev.yaml` sur `docker.lab` et `prod.yaml` sur `docker-client.lab`, dans
`/opt/lab-compose-env`. Le setup transfère la même archive d'image par SSH,
sans reconstruire l'image sur la VM de production. Fusionnez la base d'abord,
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
et les données de l'autre VM. Aucune copie manuelle, construction ni téléchargement
n'est nécessaire. Les contrôles recréent indépendamment les projets avec données
aléatoires. Ils comparent le digest de l'image préparée aux deux images exécutées
et refusent un build Compose pendant le déploiement.
