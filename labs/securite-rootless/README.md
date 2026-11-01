# securite-rootless

**Audience:** learners.

Qualify the unprivileged daemon, its network and persistent data.

## What you will practice

The dedicated service is active and its real owner is unprivileged. The
rootless HTTP workload responds, the network refuses an outside peer and data
survives recreation. Explain UID mapping and the separate image store without
confusing root inside the container with root on the host.

## Safety boundaries

Only lab-labelled containers, volumes and files are changed. System-level exercises use dedicated lab accounts or restore the original daemon configuration. Disk pressure is simulated by a bounded 16 MiB volume and never fills the host filesystem.

## Validation

Tests inspect effective state on `docker.lab`; they do not award points for command history or file intent. Assertion messages are bilingual.
