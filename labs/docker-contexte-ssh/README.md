# docker-contexte-ssh

**Audience:** learners.

Create and use a named context for the prepared loopback SSH daemon.

## What you will practice

The named context reaches the lab daemon over SSH; the default context remains selected.

## Safety boundaries

Only lab-labelled containers, volumes and files are changed. System-level exercises use dedicated lab accounts or restore the original daemon configuration. Disk pressure is simulated by a bounded 16 MiB volume and never fills the host filesystem.

## Validation

Tests inspect effective state on `docker.lab`; they do not award points for command history or file intent. Assertion messages are bilingual.
