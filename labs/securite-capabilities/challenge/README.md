# Brief

Work on `docker.lab`, in `/opt/dsoxlab-securite-capabilities`.

1. Keep one running Compose service `worker`, project
   `dsoxlab-securite-capabilities`, label `dsoxlab.lab=securite-capabilities`.
2. Drop ALL capabilities and add only NET_BIND_SERVICE.
3. PID 1 must have exactly bit 10 set in its effective mask.
4. Keep the root-owned `/proof` file: changing its owner to UID 123 must fail.

Preserve the pinned image and bounded resources. Use Compose v2 or
`docker-compose` with the explicit project name. No daemon changes.
