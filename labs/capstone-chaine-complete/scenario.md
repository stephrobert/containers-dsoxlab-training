# Delivery assessment: no prescribed repair recipe

Prerequisites: the previous three level capstones. The source is `docker.lab`;
fresh-host recovery uses `docker-client.lab`. Work in the supplied
`/opt/lab-delivery` workspaces. An incomplete API/PostgreSQL delivery and a
loopback registry are supplied. Do not use workstation Docker or change the daemon.

Deliver a working release:

* Preserve the supplied API contract: `GET /ready`, `POST /items` with
  `{"key":"...","value":"..."}`, `GET /items/KEY`. Database `delivery`, user
  `delivery`; all requests must genuinely use PostgreSQL.
* Build `/source` in multiple stages with BuildKit. Use its offline hashed
  wheel, a pip cache mount and required build secret `build_token`. Record only
  the SHA-256 of that secret in `/app/build-receipt`; never copy raw secrets or
  build wheels into the runtime. Final image runs as UID/GID 10001.
* Publish `127.0.0.1:15088/delivery/api:1.0`, resolve its registry digest,
  explicitly pull by digest and put `API_IMAGE=...:1.0@sha256:...` in
  `release.env`. Retain `delivery.json` with `image_id`, `registry_digest`,
  `reference` and `pulled_id`, linking all stages to the same immutable image.
* Generate `sbom.spdx.json` from the actual final image using supplied
  `/app/sbom.py IMAGE_ID` (or an equivalent actual inventory). Include Debian
  and Python packages, psycopg2-binary version and the API source SHA-256.
* Project name **dsoxlab-delivery**, services **api/db**. API listens only on
  `127.0.0.1:18088`; PostgreSQL has no published port. Network `backend` is
  internal and shared only by api/db; api also joins `frontend`. Mount the
  named volume `data` at PostgreSQL's data directory. Use file secret
  `db_password`, never plaintext password environment variables.
* API: non-root, read-only root filesystem, drop all capabilities, no-new-
  privileges, memory ≤128 MiB, CPU ≤0.5. DB: memory ≤256 MiB, CPU ≤0.5.
  Both need working healthchecks; gate API startup on healthy PostgreSQL.
* Keep all ownership labels. The API's data must survive container replacement.
  Create executable `recover.sh` with no arguments: it restores availability
  and canonical runtime configuration without deleting data or rebuilding
  the published release.
* Create executable `restore.sh` with no arguments. Transfer a consistent
  PostgreSQL dump, the exact accepted image and its deployment configuration
  over the dedicated SSH identity `restore-key` to the address in `restore-host`.
  Restore both services on the second VM as **dsoxlab-delivery-restore**, with
  the API on `127.0.0.1:18089`. Preserve isolation and runtime protections,
  do not publish the database, and do not rebuild or pull the API. The evaluator
  compares all source rows and queries newly written business data through
  the restored API.
* Create executable `rollback.sh` with no arguments. A distinct faulty image
  will replace the healthy API. Restore the accepted image identity recorded
  in `delivery.json` and its canonical configuration without losing data.
  Check the live database schema before rollback: the accepted API expects
  `public.items(key text, value text)`. An injected additional required column
  without a default makes old writes incompatible. Refuse this blind rollback,
  report a schema error, and preserve existing rows. An image rollback is not
  a data migration reversal: explain the tested restoration or forward-migration
  decision to a human reviewer, especially for irreversible migrations.
* Demonstrate business readiness failure while PostgreSQL is interrupted, then
  successful reads after it returns without restarting the existing API.
  Docker does not automatically restart a container solely because it is unhealthy.
* Create executable `maintenance.sh` with no arguments. Record measured engine
  inventory in `maintenance.json` (`containers`, `images`, `volumes`, `networks`;
  include container/image `Id` and volume `Name`, but no secret environment
  values). Save a consistent custom-format database dump as `maintenance.dump`
  before removal. Remove only this lab's stopped containers and unused networks
  or volumes explicitly labelled `dsoxlab.maintenance=jetable`. Preserve stopped
  data-bearing objects labelled `preserve`, all active services and every other
  owner's resources. The evaluator probes business reads throughout the command,
  requires completion within 45 seconds and actually restores the backup into
  a separate scratch database.
* Write `RUNBOOK.md` describing dependencies, exposed access, inventory decisions,
  recovery and rollback commands, backup restoration checks and service limits.
  Human review must distinguish the measured 45-second maintenance window from
  production SLO/RPO/RTO commitments. This two-VM recovery exercise does not
  establish high availability or native ARM64 support.

After delivery, eight incidents can be injected with
`python3 incidents.py NUMBER` (1–8). Their causes are intentionally not listed
here. Observe health, logs, networks, mounts and configuration; recover without
losing a previously written item. The evaluator really injects each incident,
measures failure, runs `recover.sh`, and checks availability and data again.

The lab registry is intentionally HTTP **on loopback only**, not a production
registry lesson. No global prune, shared network changes, host service restart
or external image publication. Setup needs apt and three pinned image pulls;
subsequent builds, SBOM inventory and tests use local data. Required: amd64 VM,
Docker with BuildKit/cache/secret mounts, Compose v2 with `up --wait`, Python 3,
and free loopback ports 15088/18088 on the source and 18089 on the second VM.
Compose must support `!override` when used to replace the API publication.
The bundled driver wheel requires amd64
and CPython 3.13 with glibc. Public training tokens are not real credentials.
