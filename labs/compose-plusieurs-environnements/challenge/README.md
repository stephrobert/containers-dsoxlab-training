# Operate two environments without cross-talk

Follow `/opt/MISSION.md`. Keep the base declaration and write dev/prod overrides.
Dev runs on `docker.lab`, production on `docker-client.lab`. Checks inspect both
running deployments, compare their real image IDs with the prepared source
artifact and refuse Compose build directives. Replacing either deployment must
preserve its data without touching the other.
