# Unbounded logs, on the whole machine

## The situation

On `docker.lab`, a container created without any option keeps a log that is far
too big. Setting each container by hand does not hold: forgetting one is enough.
The limit must come from the daemon.

## Mission

Configure the daemon so that every **new** container, created without any log
option, gets:

- the `json-file` driver;
- files of `1m` at most;
- `2` files kept.

Do not lose any other setting of the daemon. The brief is also written to
`/opt/dsoxlab-docker-configurer-le-demon/MISSION.md`.

## What is graded

The checks create their own containers, without any log option:

1. the driver, the size and the number of files are those requested;
2. the limit really acts: on a log that exceeds it, the first lines have been
   dropped and the volume kept fits the budget.

The configuration file is not read: only what a new container receives counts.
The test containers are removed, and the lab's cleanup puts the starting
configuration back.
