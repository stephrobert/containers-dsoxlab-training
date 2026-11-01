# Keep fresh writes when containers disappear

Follow `/opt/MISSION.md`. Write `/opt/lab-compose-persist/compose.yaml` with a named
volume. Checks replace the container twice and require the same data volume and
random application writes to survive, then restore the original content.
