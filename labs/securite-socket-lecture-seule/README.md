# securite-socket-lecture-seule

**Audience:** learners.

Remove the host socket mount; read-only on a Unix socket does not create a read-only API.

## What you will practice

The labelled application container has no mount of the host Docker socket.

## Safety boundaries

Only lab-labelled containers, volumes and files are changed. System-level exercises use dedicated lab accounts or restore the original daemon configuration. Disk pressure is simulated by a bounded 16 MiB volume and never fills the host filesystem.

## Validation

Tests inspect effective state on `docker.lab`; they do not award points for command history or file intent. Assertion messages are bilingual.
