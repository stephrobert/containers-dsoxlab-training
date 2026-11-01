# Challenge notes

Use the per-run values in `state.env`; database names are randomized so cleanup
does not touch a pre-existing database with a common name. The grade restores
the dump independently, so copying rows directly into the target database is
not sufficient. The target is `docker-client.lab`, not another database on
`docker.lab`. The transferred file must have the same SHA-256 checksum as the
source backup.
