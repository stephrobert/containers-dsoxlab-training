# securite-rootless

**Audience:** learners.

Start only the dedicated unprivileged daemon and verify its rootless identity.

## What you will practice

The dedicated service is active and its daemon reports rootless mode.

## Safety boundaries

Only lab-labelled containers, volumes and files are changed. System-level exercises use dedicated lab accounts or restore the original daemon configuration. Disk pressure is simulated by a bounded 16 MiB volume and never fills the host filesystem.

## Validation

Tests inspect effective state on `docker.lab`; they do not award points for command history or file intent. Assertion messages are bilingual.
