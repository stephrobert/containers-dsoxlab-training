# Brief

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
