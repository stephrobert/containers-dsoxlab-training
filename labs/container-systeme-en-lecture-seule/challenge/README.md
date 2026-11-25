# A worker that should not rewrite its system

## The situation

On `docker.lab`, the `worker` of project `dsoxlab-container-systeme-en-lecture-seule`
writes the time in `/run/heartbeat` every second. It is its only write, and yet
its whole root is writable. The project is in
`/opt/dsoxlab-container-systeme-en-lecture-seule`.

## Mission

1. The root is read-only: a real write in `/` fails.
2. `/run` is a writable tmpfs of exactly 4 MiB, with `noexec` and `nosuid`.
3. The worker runs and `/run/heartbeat` keeps moving forward.

Keep the project, the `dsoxlab.lab=container-systeme-en-lecture-seule` label, the
supplied command, the pinned image and the resource limits. Add no host mount and
do not change the daemon. The check makes a few small writes in the container,
then removes them.
