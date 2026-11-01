# Challenge

Implémentez `/opt/lab-compose-ci/ci.sh` selon [le contrat](../scenario.fr.md).
Quatre contrôles exécutent succès, échec, sources commitées distinctes et refus
d'une source non commitée. Les archives acceptées sont rechargées et comparées
au commit réel, à l'identité d'image et au SHA-256 ; un échec ne publie rien.
Tous échouent avant intervention. Tests applicatifs et artefacts réels produisent
les preuves ; le YAML ne suffit pas.
