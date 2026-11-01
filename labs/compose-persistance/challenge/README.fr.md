# Garder les nouvelles écritures quand les conteneurs disparaissent

Suivez `/opt/MISSION.md`. Écrivez `/opt/lab-compose-persist/compose.yaml` avec un
volume nommé. Les contrôles remplacent deux fois le conteneur et exigent la
conservation du même volume et des écritures aléatoires, puis restaurent l'original.
Utilisez UID/GID 10001, racine en lecture seule et `/data` appartenant à
10001:10001, mode 0700. Les accès imprévus doivent rester refusés après remplacement.
