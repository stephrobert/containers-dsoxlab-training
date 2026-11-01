# Grant only the required secret

Follow `/opt/MISSION.md` and write `/opt/lab-compose-secret/compose.yaml`.
Checks measure app's read-only access, observer denial, absence of metadata/log
leaks, effective Git exclusion, actual reachable Git history without credentials,
the protected prepared image identity and consumption after temporary rotation.
