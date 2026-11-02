# Accorder seulement le secret nécessaire

Suivez `/opt/MISSION.md` et écrivez `/opt/lab-compose-secret/compose.yaml`.
Les contrôles mesurent l'accès en lecture seule de app, le refus pour observer,
l'absence de fuite dans les métadonnées, journaux et blobs Git accessibles,
l'exclusion Git effective, l'identité protégée de l'image fournie et la mise en
service de la valeur suivante, que vous effectuez vous-même : le lab pose
`credentials/token-next.txt`, et le contrôle lit l'état final, l'empreinte et
l'âge du conteneur.
