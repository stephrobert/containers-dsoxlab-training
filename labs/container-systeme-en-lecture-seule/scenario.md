# A worker that should not rewrite its system

The worker updates `/run/heartbeat` every second. Its entire root filesystem is
writable even though only runtime storage is needed.

In `/opt/dsoxlab-container-systeme-en-lecture-seule`, make the root filesystem
read-only without stopping that heartbeat. Give `/run` a writable 4 MiB tmpfs,
with noexec and nosuid. Keep project
`dsoxlab-container-systeme-en-lecture-seule` and its lab label.

Do not make host mounts read-only, change daemon settings or mount host paths.
The checker makes tiny disposable writes only inside this container.
