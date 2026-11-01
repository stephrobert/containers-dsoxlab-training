# A finished migration is not a running service

Image `dsoxlab-compose-migrate:app` supplies two scripts:
`/usr/local/bin/migrate.sh` creates a SQLite schema transactionally and records
version 1; `/usr/local/bin/app.sh` refuses to start without that schema.
Both use `/data/app.db`. No containers or database volumes exist initially.

## Mission

Write `/opt/lab-compose-migrate/compose.yaml`, project `dsoxlab-migration`.
Declare services `migrate` and `app`, both using the supplied image and scripts.
Share a writable named volume at `/data`, with no other mounts or replacement entrypoints.
The migration is a one-shot job: it must exit 0, with restart policy `"no"`.
The application must wait for `service_completed_successfully`, not merely
`service_started`, and remain running after migration.

Replaying `docker compose run --rm --no-deps migrate` must preserve existing
records and leave exactly one migration version marker. Do not put migrations
inside the application's command or manually create the schema.

The check inserts and removes a random record, runs migration twice, and uses
two separate disposable projects to verify startup with an empty volume and
an intentional migration exit 42. In the failure case app must never start.
Do not set explicit global volume/container/network names or `name:` for the
project: different `-p` values must isolate these trial resources.
