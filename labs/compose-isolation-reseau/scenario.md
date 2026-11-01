# An API bridges two trust zones

Three local images are ready on `docker.lab`, but no containers run:

- `dsoxlab-compose-net:front` relays `/cgi-bin/value` to `http://api:8080/cgi-bin/value`;
- `dsoxlab-compose-net:api` relays `/cgi-bin/value` to `http://data:8080/value.txt`;
- `dsoxlab-compose-net:data` serves `/value.txt` on port `8080`.

## Mission

Write `/opt/lab-compose-net/compose.yaml`, project `dsoxlab-isolation-reseau`.
Declare exactly three services named `front`, `api` and `data` using their supplied
images and commands, without mounts, privileged mode or extra capabilities.

Create two Compose-managed bridge networks:

- a non-internal frontend network shared only by `front` and `api`;
- an internal backend network shared only by `api` and `data`.

Do not attach any additional networks. Publish only `front` on
`127.0.0.1:18088:8080`. Neither API nor data may publish host ports.
The endpoint `http://127.0.0.1:18088/cgi-bin/value` must relay live data through
the API. Direct access from `front` to `data:8080` must fail, including when
using the data container's IP instead of its DNS name.

Keep service discovery by name; do not hardcode IP addresses or change Docker's
global firewall. The declaration must recreate all services without builds,
pulls or manual steps. Checks temporarily change and restore live data, and
repeat the isolation test after force-recreating the application.

`internal: true` restricts the backend's external connectivity; it does not
replace separating network memberships. The dual-attached API can access both
zones, so this topology is not a defense against a compromised API.
