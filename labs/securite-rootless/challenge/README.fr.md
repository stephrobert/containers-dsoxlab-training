# Contrat fonctionnel : securite-rootless

Les tests inspectent le démon rootless réel et l'UID de son processus systemd
sur `docker.lab`. Le workload de son stockage distinct publie HTTP seulement
sur loopback non privilégié, autorise un pair réseau, refuse un pair sans réseau
et conserve une donnée nouvelle sur volume après deux recréations. Les objets
d'essai ont des noms uniques bornés et sont retirés, même après allocation
partielle. L'état initial ne rapporte aucun point.
