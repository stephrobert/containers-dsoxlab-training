# securite-socket-lecture-seule

**Audience:** learners.

Remove the capability to reach the daemon socket instead of restricting it:
read-only applies to the socket file, not to the requests travelling through
it.

## What you will practice

First observe that a stop `POST` succeeds through a socket mounted `:ro`, then
remove that mount from the application container, by any indirect path too.

## Safety boundaries

Only the containers and the work directory carrying this lab's label are
changed. The witness you will stop exists only for the demonstration and is
removed at cleanup, as are the two pinned images, but only if this lab pulled
them.

The daemon socket itself is never modified: the lab removes a mount, it touches
neither the daemon configuration nor the file permissions.

## Validation

Both checks inspect effective state on `docker.lab`; neither command history
nor file contents award points. Neither compares file names: one resolves mount
sources on the host, the other collects the inode of every socket visible
inside the container. Assertion messages are bilingual.
