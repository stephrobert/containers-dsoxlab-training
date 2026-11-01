# Two images are not yet an application

On `docker.lab`, two images are prepared, but no services run:

- `dsoxlab-compose-first:api` serves `/release.txt` on port `8080`;
- `dsoxlab-compose-first:web` serves `/cgi-bin/release` on port `8080` and
  retrieves the API's current content using `http://api:8080/release.txt`.

The web image therefore needs service discovery, not a hardcoded container IP.
No public images need to be downloaded; both images were built from pinned Alpine.

## Mission

Write `/opt/lab-compose-first/compose.yaml` and start it as Compose project
`dsoxlab-premiere-stack`:

- exactly two running services, named `api` and `web`, using the supplied images;
- a shared user-defined network where `api` resolves by service name;
- web port `8080` published only on `127.0.0.1:18086`;
- no API port published on the host;
- `http://127.0.0.1:18086/cgi-bin/release` relays the live API release.

The declaration must recreate both services with a single Compose invocation,
without manual container setup, builds or pulls. Keep the supplied commands and
image contents unchanged; do not mount replacement application files.
Use the same project name on each invocation so Compose manages one application.

The check changes the API's live content briefly and expects web to relay it,
then restores it. It also force-recreates both containers from your declaration.
Do not rely on transient manual modifications inside containers.

```bash
docker compose -p dsoxlab-premiere-stack \
  -f /opt/lab-compose-first/compose.yaml ps
```
