# A service that stops when everything is taken away

A small job launcher was deployed with Docker's default capabilities. It runs
each of its jobs inside a **cell**: a directory it confines the job to with
`chroot`. It reports its state every second in `/run/lanceur/etat`.

The security review asks for the least privilege, and the advice is known:
drop every capability, then give back what the service needs. Nobody knows
which one that is. Dropping all of them and restarting is not enough: **the
launcher stops at startup**.

Only this disposable project is in scope. Do not change the daemon, do not use
privileged mode, and do not touch another container.

## Mission

Work on `docker.lab`, in `/opt/dsoxlab-securite-capabilities`.

1. Keep one running Compose service `worker`, project
   `dsoxlab-securite-capabilities`, label `dsoxlab.lab=securite-capabilities`.
2. Drop ALL capabilities and add back **exactly one**: the one the launcher
   needs. The container is not privileged.
3. The launcher must run: its report in `/run/lanceur/etat` says `ok`, and the
   count that follows it keeps going up.
4. PID 1 must carry that single capability in its effective mask, and no other.
5. Keep the root-owned `/proof` file: changing its owner to UID 123 must fail.

Find which capability it is by reading what the launcher says when it stops:
its logs name the operation that is refused. Do not guess from a list.

Preserve the pinned image and bounded resources. Use Compose v2 or
`docker-compose` with the explicit project name. No daemon changes.
