# Épreuve de livraison : sans recette de réparation

Prérequis : les capstones des trois niveaux précédents. La source est
`docker.lab` ; la restauration utilise `docker-client.lab`. Travaillez dans
les espaces fournis `/opt/lab-delivery`. Une livraison API/PostgreSQL
incomplète et un registre local sont fournis. Ni Docker du poste ni modification
du démon.

Livrez une version opérationnelle :

* Conservez le contrat API : `GET /ready`, `POST /items` avec
  `{"key":"...","value":"..."}`, `GET /items/CLE`. Base et utilisateur
  `delivery` ; les requêtes utilisent réellement PostgreSQL.
* Construisez `/source` en plusieurs étapes avec BuildKit : wheel locale
  vérifiée, cache pip, secret obligatoire `build_token`. Enregistrez seulement
  son SHA-256 dans `/app/build-receipt` ; aucun secret brut ni wheel de build
  dans le runtime. UID/GID final 10001.
* Publiez `127.0.0.1:15088/delivery/api:1.0`, résolvez le digest du registre,
  tirez explicitement par digest puis écrivez `API_IMAGE=...:1.0@sha256:...`
  dans `release.env`. Conservez `delivery.json` avec `image_id`,
  `registry_digest`, `reference`, `pulled_id`, liés à la même image immuable.
* Générez `sbom.spdx.json` depuis l'image finale réelle avec
  `/app/sbom.py ID_IMAGE` fourni, ou inventaire réel équivalent : paquets
  Debian/Python, version psycopg2-binary et SHA-256 du code API.
* Projet **dsoxlab-delivery**, services **api/db**. API publiée seulement sur
  `127.0.0.1:18088` ; PostgreSQL sans port publié. Réseau `backend` interne,
  partagé uniquement par api/db ; api rejoint aussi `frontend`. Volume nommé
  `data` sur le répertoire PostgreSQL. Secret fichier `db_password`, jamais
  mot de passe en clair dans l'environnement.
* API non-root, racine en lecture seule, toutes capacités retirées,
  no-new-privileges, mémoire ≤128 Mio et CPU ≤0,5. DB mémoire ≤256 Mio et
  CPU ≤0,5. Sondes de santé fonctionnelles ; API attend PostgreSQL sain.
* Conservez tous les labels de propriété. Les données survivent au remplacement
  des conteneurs. Créez `recover.sh` exécutable sans argument : il rétablit la
  disponibilité et la configuration canonique sans supprimer les données ni
  reconstruire la version publiée.
* Créez `restore.sh` exécutable sans argument. Transférez un dump PostgreSQL
  cohérent, l'image acceptée exacte et sa configuration via l'identité SSH
  dédiée `restore-key` vers l'adresse de `restore-host`. Restaurez les deux
  services sur la seconde VM sous **dsoxlab-delivery-restore**, API sur
  `127.0.0.1:18089`. Conservez isolation et protections, sans publier la base,
  reconstruire ni tirer l'API. L'évaluation compare toutes les lignes source
  et interroge les données métier nouvelles via l'API restaurée.
* Créez `rollback.sh` exécutable sans argument. Une image fautive distincte
  remplace l'API saine. Rétablissez l'identité acceptée de `delivery.json` et
  sa configuration canonique sans perdre les données. Vérifiez le schéma réel :
  l'API acceptée attend `public.items(key text, value text)`. Une colonne
  supplémentaire obligatoire sans valeur par défaut rend les anciennes
  écritures incompatibles. Refusez ce rollback aveugle, signalez le schéma
  incompatible et préservez les lignes. Revenir à une image n'annule pas une
  migration : expliquez à un évaluateur humain le choix entre restauration
  éprouvée et migration corrective, notamment pour une migration irréversible.
* Prouvez la panne de disponibilité métier pendant l'interruption PostgreSQL,
  puis la reprise des lectures sans redémarrer l'API existante. Docker ne
  redémarre pas automatiquement un conteneur simplement parce qu'il est unhealthy.
* Créez `maintenance.sh` exécutable sans argument. Conservez l'inventaire réel
  dans `maintenance.json` (`containers`, `images`, `volumes`, `networks` ;
  `Id` des conteneurs/images et `Name` des volumes, sans valeurs secrètes
  d'environnement). Sauvegardez d'abord un dump cohérent au format custom dans
  `maintenance.dump`. Retirez seulement les conteneurs arrêtés et réseaux ou
  volumes inutilisés de ce lab explicitement labellisés
  `dsoxlab.maintenance=jetable`. Préservez les objets arrêtés porteurs de données
  labellisés `preserve`, les services actifs et les ressources des autres
  propriétaires. L'évaluation sonde les lectures métier pendant la commande,
  impose 45 secondes au maximum et restaure vraiment le dump dans une base
  d'essai séparée.
* Écrivez `RUNBOOK.md` : dépendances, accès publiés, décisions d'inventaire,
  commandes de reprise/rollback, vérifications de restauration et limites de
  service. La revue humaine distingue la fenêtre mesurée de maintenance de
  45 secondes des engagements SLO/RPO/RTO de production. Cet exercice de reprise
  à deux VM ne démontre ni haute disponibilité ni prise en charge ARM64 native.

Après livraison, huit incidents s'injectent avec `python3 incidents.py NUMERO`
(1–8). Leurs causes ne sont volontairement pas annoncées. Observez santé,
journaux, réseaux, montages et configuration ; rétablissez sans perdre un
élément écrit auparavant. L'évaluation injecte chaque incident, mesure la panne,
lance `recover.sh` puis vérifie disponibilité et données.

Le registre est volontairement HTTP **sur boucle locale uniquement**, pas une
leçon de registre de production. Aucun prune global, changement de réseau
partagé, redémarrage hôte ni publication externe. Setup : apt et trois images
épinglées ; ensuite builds, SBOM et tests utilisent des données locales.
VM amd64, Docker avec BuildKit/cache/secrets, Compose v2 (`up --wait`), Python 3
et ports source 15088/18088 et cible 18089 libres requis. Compose doit prendre
en charge `!override` si utilisé pour remplacer la publication API.
Wheel pour CPython 3.13 amd64 avec
glibc. Les tokens publics de formation ne sont pas de vrais identifiants.
