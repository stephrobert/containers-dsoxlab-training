# A backup is only useful after a restore

A PostgreSQL source database contains three order rows. The restore database
and backup file do not exist. PostgreSQL's local `postgres` account is available.
The unique database names, marker and writable backup directory are in
`/opt/lab-postgres-sauvegarde/state.env`; the expected rows are in `state.json`.

## Mission

Create a PostgreSQL custom-format dump at
`/opt/lab-postgres-sauvegarde/backup/orders.dump`. Restore it into the
`RESTORED_DB` named in `state.env`, without changing the source. Add the exact
`OWNERSHIP` comment to the restore database so cleanup can identify the
resource created for this run.

A file that merely exists is not proof: the functional check restores the dump
into a separate temporary database and compares its rows with the live source
and the named restore database. That scratch database is removed by the test.
