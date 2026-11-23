# A container is replaceable, its data is not

Image `dsoxlab-compose-persist:app` is ready on `docker.lab`. Its startup command
initializes `/data/value.txt` from `/seed/value.txt` only when the data file is absent,
then stays running. No application container or volume exists initially.

## Mission

Write `/opt/lab-compose-persist/compose.yaml`, project `dsoxlab-persistance`.
Run exactly one service `app` using the supplied image and command.
Declare a named Compose volume `data` and mount it writable at `/data`.
Do not use bind mounts, anonymous volumes, extra mounts or replacement commands.
Run the application as UID/GID 10001.
Prepare `/data` with owner 10001:10001 and mode 0700. Another UID must not
read or write the data; the application must not write outside `/data`.
These effective permissions must remain unchanged after recreation.

The initial value must be visible in `/data/value.txt`. More importantly, fresh
writes must survive both force-recreation and `docker compose down` followed by
`up`, using the same volume. Do not use `down --volumes` during normal operation.
Recreation must not need a build, pull or manual data copy.

Checks temporarily replace the data with random values, replace the container,
and restore the original content afterward. Merely reproducing the initial
seed in every new container does not prove persistence.
Cleanup intentionally deletes this project's volume after the exercise.

## Keep fresh writes when containers disappear

Follow `/opt/MISSION.md`. Write `/opt/lab-compose-persist/compose.yaml` with a named
volume. Checks replace the container twice and require the same data volume and
random application writes to survive, then restore the original content.
Use UID/GID 10001 and `/data` owned by 10001:10001, mode 0700.
Checks require unexpected reads/writes to remain denied after replacement.
