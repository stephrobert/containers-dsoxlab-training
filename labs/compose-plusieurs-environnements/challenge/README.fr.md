# Exploiter deux environnements sans interférence

Suivez `/opt/MISSION.md`. Gardez la déclaration de base et écrivez les surcharges
dev/prod. Dev tourne sur `docker.lab`, production sur `docker-client.lab`.
Les contrôles comparent les identités réelles des images à l'artefact préparé
et refusent les directives Compose de build. Remplacer un déploiement conserve
ses données sans toucher l'autre.
