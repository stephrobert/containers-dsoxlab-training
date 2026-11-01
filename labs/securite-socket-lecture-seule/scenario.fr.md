# Scénario

Un conteneur applicatif monte /var/run/docker.sock en lecture seule. L’équipe suppose que :ro bloque les appels API modifiants, ce qui n’est pas sûr.

## Mission

Le conteneur applicatif marqué ne monte pas la socket Docker de l’hôte.
