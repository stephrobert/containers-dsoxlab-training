# What is asked

On `docker.lab`, a source PostgreSQL database carries three order rows. On
`docker-client.lab`, a second VM, nothing exists yet. The unique database names,
the ownership marker and the backup directory are in
`/opt/lab-postgres-sauvegarde/state.env`; the expected rows are in `state.json`.

```text
SOURCE_DB     the database to back up, on docker.lab
RESTORED_DB   the database to create, on docker-client.lab
BACKUP_DIR    the backup directory, writable
OWNERSHIP     the exact marker to set on the restored database
```

The names are drawn at random for each session, so that cleanup never touches a
pre-existing database with a common name.

## 1. The backup exists, in custom format

`BACKUP_DIR/orders.dump` must exist and start with `PGDMP`.

The check reads the **signature**, not the extension: a plain SQL dump would
carry the same filename without being the same format. `pg_dump -Fc` produces
the custom format, the only one `pg_restore` can replay selectively.

## 2. The backup was transferred unchanged

The file must exist **at the same path** on `docker-client.lab`, with the **same
SHA-256 digest** as the one on `docker.lab`.

This is the challenge's anti-cheat, and it is worth understanding. Without this
measurement, recreating the three rows by hand on the second VM would pass every
other check: the rows would be there, so would the database, so would the
marker. The digest requires that the file used be **the one that was produced**,
and it is the only measurement that tells a restore from a copy.

## 3. The target service answers, and the database carries its marker

Two things, in this order: PostgreSQL must answer a real query on
`docker-client.lab`, then `RESTORED_DB` must exist there with the **exact**
`OWNERSHIP` comment.

The order matters. If the service is silent, every question about a database
returns the same error, and a check that did not tell them apart would send you
creating a database when it is the engine that needs starting.

## 4. The restored database carries every row, and the source has not moved

The rows of `RESTORED_DB` are compared to the expected set, **ordered** rather
than counted: three rows with one changed value give the same count as three
correct rows.

And the source is verified right here: its rows **and** its marker. Restoring
onto `docker.lab` instead of the second VM does not satisfy this challenge, and
a `dropdb` followed by a `createdb` would erase the comment without touching the
rows.

## 5. The backup restores into a fresh database

The check creates a disposable database on `docker-client.lab`, replays your
backup into it, compares the rows, then drops it.

This is the difference between "it works today" and "the backup is good". The
previous checks observe a state; this one answers the only question that matters
the day you need it: does this file reproduce the database, elsewhere, from
nothing?

## What is not graded, and why we tell you

Before replaying your backup, check 5 verifies that `pg_restore` **refuses** an
invalid file. This is not a requirement for you: you can neither cause it nor
fail it. It is the condition for the success reported afterwards to mean
anything, because a tool that reported success on an empty file would prove
nothing about yours. If that guard fails, the message tells you it is not your
fault.
