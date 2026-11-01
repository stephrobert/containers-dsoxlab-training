# Bring the stack back into service

The local image `dsoxlab-compose-capstone:service` contains two roles. `writer`
copies a supplied release marker into `/data` and exits; `web` serves that file
on port 8080. No application containers or volumes exist yet.

## Mission

Create `/opt/lab-compose-capstone/compose.yaml` for project
`dsoxlab-compose-capstone`. Define exactly two services using the supplied
image: `writer` with `ROLE=writer`, and `web` with `ROLE=web`. Use a named
volume mounted at `/data` by both services. The writer must be the successful
one-shot prerequisite for web; web must mount the data read-only.

Keep web healthy and publish `8080` only as `127.0.0.1:18092`. Start the stack
in the background. The endpoint `/release.txt` must return the supplied
release marker. Recreating only web must not recreate writer or lose the data.
The tests perform that bounded recreation and leave the stack running.
