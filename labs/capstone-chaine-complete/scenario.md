# Delivery assessment: no prescribed repair recipe

Prerequisites: the previous three level capstones. Work only on `docker.lab`
in `/opt/lab-delivery`. An incomplete API/PostgreSQL delivery and a loopback
registry are supplied. Do not use workstation Docker or change the daemon.

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
and free loopback ports 15088/18088. The bundled driver wheel requires amd64
and CPython 3.13 with glibc. Public training tokens are not real credentials.
