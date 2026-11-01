# PostgreSQL backup and restore

The functional check verifies a real PostgreSQL custom-format dump by
restoring it into a fresh scratch database on `docker-client.lab` and comparing actual rows with
the source and requested restore database. The test removes its own scratch
database even when a check fails.

Cleanup drops only databases carrying this run's random ownership marker and
removes the lab's own backup directory on both VMs. The validator photographs
both Docker engines, not only the primary target. The invalid-backup check must
fail explicitly; neither a copied row list nor a local-only restore is sufficient.
