# A container is replaceable, its data is not

Image `dsoxlab-compose-persist:app` is ready on `docker.lab`. Its startup command
initializes `/data/value.txt` from `/seed/value.txt` only when the data file is absent,
then stays running. No application container or volume exists initially.

## Mission

Write `/opt/lab-compose-persist/compose.yaml`, project `dsoxlab-persistance`.
Run exactly one service `app` using the supplied image and command.
Declare a named Compose volume `data` and mount it writable at `/data`.
Do not use bind mounts, anonymous volumes, extra mounts or replacement commands.

The initial value must be visible in `/data/value.txt`. More importantly, fresh
writes must survive both force-recreation and `docker compose down` followed by
`up`, using the same volume. Do not use `down --volumes` during normal operation.
Recreation must not need a build, pull or manual data copy.

Checks temporarily replace the data with random values, replace the container,
and restore the original content afterward. Merely reproducing the initial
seed in every new container does not prove persistence.
Cleanup intentionally deletes this project's volume after the exercise.
