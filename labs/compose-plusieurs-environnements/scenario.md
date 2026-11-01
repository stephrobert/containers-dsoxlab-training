# One application, two independent deployments

`/opt/lab-compose-env/compose.yaml` supplies a base service `app` with a named
data volume and placeholder environment/memory settings. Keep this base unchanged.
The supplied image serves its `APP_ENV` at `/environment.txt` on port 8080 and
initializes `/data/value.txt` only if missing. No deployments run initially.

## Mission

Write overrides `dev.yaml` and `prod.yaml` in the same directory. Merge the base
first, then the selected override with two `-f` options. Run both projects simultaneously:

| Override | Project | APP_ENV | Memory | Publication |
|---|---|---|---|---|
| dev.yaml | dsoxlab-env-dev | development | 64 MiB | 127.0.0.1:18090:8080 |
| prod.yaml | dsoxlab-env-prod | production | 128 MiB | 127.0.0.1:18091:8080 |

Each project must have exactly one app, its own named data volume and its own
network. Keep supplied image/command and the inherited volume mount, without
replacement mounts, global resource names or shared external resources.

The two HTTP endpoints must report their actual environment. Force-recreating
one project must preserve fresh data in its volume and leave the other container's
identity and data unchanged. No manual copies, builds or downloads are needed.
Checks perform these independent recreations with random data and restore the original.
