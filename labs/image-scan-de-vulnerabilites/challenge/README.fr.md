# Un scan est une preuve datée

## La situation

Sur `docker.lab`, `/opt/lab-image-scan` contient deux images de bibliothèques
Debian : `legacy` porte OpenSSL 1.1.1n, `fixed` porte OpenSSL 3.0.17. Ce sont des
échantillons sans leurs dépendances : **ne les exécutez jamais** et ne les publiez
pas. Leurs sources et leurs sommes sont dans `fixtures/PROVENANCE.md`.

Le scan se fait hors ligne, avec **debsecan**, sur une base Debian figée au
2026-11-01 11:37:02 UTC. Il lit l'inventaire des paquets Debian, pas toutes les
dépendances ni tous les fichiers. La machine doit être en amd64.

## Mission

1. Lancez `python3 scan.py dsoxlab-scan:legacy legacy-report.json` ; utilisez
   `/usr/bin/python3` pour les paquets système. Le script extrait l'inventaire
   de l'image sans démarrer le conteneur, lance **debsecan** sur la base locale
   et retourne 1 quand la politique refuse l'image.
2. Lisez toutes les alertes. La politique ciblée refuse **CVE-2023-0286**,
   le vrai défaut de confusion de types X.400 d'OpenSSL ; elle ne prétend pas
   que l'image corrigée n'a aucune autre vulnérabilité.
3. Promouvez l'image `fixed` fournie vers `dsoxlab-scan:candidate`, scannez-la
   vers `candidate-report.json` en conservant alertes et champs de provenance.
4. Créez un `gate.sh IMAGE RAPPORT` exécutable qui lance un scan frais fourni,
   conserve le JSON et retourne son statut. Prouvez le refus de legacy et
   l'acceptation de fixed. Ne filtrez, modifiez ni inventez les résultats.

Au départ, il n'y a ni rapport valable, ni candidat, ni barrière. Les trois contrôles
refont le scan et comparent vos preuves : alertes, identifiants d'images, empreintes
de l'inventaire et de la base. Une preuve expire après 24 heures.
