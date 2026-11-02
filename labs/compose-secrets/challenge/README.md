# Grant only the required secret

Follow `/opt/MISSION.md` and write `/opt/lab-compose-secret/compose.yaml`.
Checks measure app's read-only access, observer denial, absence of metadata/log
leaks, effective Git exclusion, actual reachable Git history without credentials,
the protected prepared image identity and the next value put in service, which
you do yourself: the lab lays down `credentials/token-next.txt`, and the check
reads the final state, the fingerprint and the container's age.
