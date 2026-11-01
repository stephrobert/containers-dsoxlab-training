# Vrais scans d'images hors ligne

Lab guidé c4, 45 minutes. Lire [la mission](scenario.fr.md) et
[la provenance](fixtures/PROVENANCE.md). Vraies sorties debsecan sur de vrais
paquets Debian, ni CVE inventée ni pari sur une image publique mutable.

VM Debian 13 amd64, Docker, dpkg, `/usr/bin/python3`, python3-apt et debsecan
requis (apt au setup). Base et paquets versionnés ; builds et scans hors ligne.
Nettoyage limité aux images et conteneurs d'extraction du lab ainsi qu'à
`/opt/lab-image-scan`. Aucun service vulnérable n'est lancé. La politique cible
CVE-2023-0286, pas « zéro vulnérabilité ». Référence chiffrée :
`solution/image-scan-de-vulnerabilites/solution.yaml`.
