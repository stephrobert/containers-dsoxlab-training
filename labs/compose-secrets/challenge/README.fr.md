# Accorder seulement le secret nécessaire

Suivez `/opt/MISSION.md` et écrivez `/opt/lab-compose-secret/compose.yaml`.
Les contrôles mesurent l'accès en lecture seule de app, le refus pour observer,
l'absence de fuite dans les métadonnées, journaux et blobs Git accessibles,
l'exclusion Git effective, l'identité protégée de l'image fournie et la
consommation après rotation temporaire.
