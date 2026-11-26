# One application, two independent deployments

`/opt/lab-compose-env/compose.yaml` supplies a base service `app` with a named
data volume and placeholder environment/memory settings. Keep this base unchanged.
The supplied image serves its `APP_ENV` at `/environment.txt` on port 8080 and
initializes `/data/value.txt` only if missing. No deployments run initially.

## Mission

Write `dev.yaml` on `docker.lab` and `prod.yaml` on `docker-client.lab`, both
under `/opt/lab-compose-env`. The setup transfers the same image archive over
SSH; it does not rebuild the image on the production VM. Merge the base
first, then the selected override with two `-f` options. Run both projects simultaneously:

| Override | Project | APP_ENV | Memory | Publication |
|---|---|---|---|---|
| dev.yaml | dsoxlab-env-dev | development | 64 MiB | 127.0.0.1:18090:8080 |
| prod.yaml | dsoxlab-env-prod | production | 128 MiB | 127.0.0.1:18091:8080 |

Each project must have exactly one app, its own named data volume and its own
network. Keep supplied image/command and the inherited volume mount, without
replacement mounts, global resource names or shared external resources.

The two HTTP endpoints must report their actual environment. Force-recreating
one project on its VM must preserve fresh data in its volume and leave the other VM's container
identity and data unchanged. No manual copies, builds or downloads are needed.
Checks compare the prepared image digest with both running images, prohibit a
Compose deployment build and perform independent recreations with fresh data.
