# Running does not mean ready

Images `dsoxlab-compose-health:backend` and `:app` are ready, but no containers run.
Backend immediately serves `/live` on port 8080, then exposes `/ready` after four
seconds. App requests `http://backend:8080/ready` once at startup, without retries.
It exits on failure, or records `ready` in `/tmp/observed` and stays running.

## Mission

Write `/opt/lab-compose-health/compose.yaml`, project `dsoxlab-health`.
Run exactly `backend` and `app` with supplied images and commands, no mounts,
published ports, restart policies or additional startup waits.
Give backend a healthcheck against `/ready`, not `/live` or a process listing.
Use a short interval and enough startup grace for an eight-second initialization;
loss of readiness must become unhealthy within 30 seconds.
Gate app with `depends_on` condition `service_healthy`.

The check removes `/ready` while the HTTP process and `/live` stay available,
then restores it. It also starts isolated projects with a slower backend and
a backend that never becomes ready. App must wait in the first case and never
start in the second. Do not hardcode global container or network names.

Compose's health dependency gates initial startup; it does not automatically
stop or restart an already-running dependent when backend becomes unhealthy.
