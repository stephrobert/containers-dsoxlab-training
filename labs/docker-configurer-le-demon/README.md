# docker-configurer-le-demon

**Audience:** learners.

Merge bounded json-file log defaults into the daemon configuration.

## What you will practice

Newly created containers use the requested defaults; cleanup restores the original daemon configuration.

## Safety boundaries

Only lab-labelled containers, volumes and files are changed. System-level exercises use dedicated lab accounts or restore the original daemon configuration. Disk pressure is simulated by a bounded 16 MiB volume and never fills the host filesystem.

## Validation

Tests inspect effective state on `docker.lab`; they do not award points for command history or file intent. Assertion messages are bilingual.
