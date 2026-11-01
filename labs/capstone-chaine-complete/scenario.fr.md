# Épreuve de livraison : sans recette de réparation

Prérequis : les capstones des trois niveaux précédents. Travaillez uniquement
sur `docker.lab`, dans `/opt/lab-delivery`. Une livraison API/PostgreSQL
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
et ports locaux 15088/18088 libres requis. Wheel pour CPython 3.13 amd64 avec
glibc. Les tokens publics de formation ne sont pas de vrais identifiants.
