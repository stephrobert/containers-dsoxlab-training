# PostgreSQL backup and restore

The functional check verifies a real PostgreSQL custom-format dump by
restoring it into an isolated scratch database and comparing actual rows with
the source and requested restore database. The test removes its own scratch
database even when a check fails.

Cleanup drops only databases carrying this run's random ownership marker and
removes the lab's own backup directory.
