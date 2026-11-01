# Un scan est une preuve datée, pas un certificat permanent

Sur `docker.lab`, travaillez dans `/opt/lab-image-scan`. Deux images scratch
de **bibliothèques témoins** contiennent les fichiers et inventaires de vrais
paquets Debian. Ce ne sont pas des services : ne les exécutez jamais.
`legacy` contient OpenSSL 1.1.1n et `fixed` OpenSSL 3.0.17.
[PROVENANCE.md](fixtures/PROVENANCE.md) donne les sources et SHA-256 exacts.
La base Debian originale est figée au 2026-11-01 11:37:02 UTC : elle ne dépend
pas de l'état d'une image publique demain.

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

Aucun rapport réussi, tag candidat ou gate au départ. L'évaluation compare les
preuves aux sorties réelles d'un nouveau scan, aux ID d'images et aux hash des
inventaires et de la base. Les preuves expirent après 24 heures.
Il s'agit de métadonnées de paquets Debian, **pas** d'un scan exhaustif des
dépendances applicatives ou du système de fichiers. Les fixtures scratch
omettent les dépendances : témoins non exécutés, pas applications déployables.

Toutes les données sont locales ; apt installe `debsecan`, `python3-apt`,
Docker et dpkg au setup. Puis scans et builds sont hors ligne. Les paquets
témoins sont amd64 ; VM amd64 requise. Ne publiez jamais ces images témoins
dans un registre public.
