# docker-rotation-des-journaux

**Audience:** learners.

Replace the labelled demo service with bounded per-container json-file rotation.

## What you will practice

The service uses json-file logs capped at 1 KiB with three retained files.

## Safety boundaries

Only lab-labelled containers, volumes and files are changed. System-level exercises use dedicated lab accounts or restore the original daemon configuration. Disk pressure is simulated by a bounded 16 MiB volume and never fills the host filesystem.

## Validation

Tests inspect effective state on `docker.lab`; they do not award points for command history or file intent. Assertion messages are bilingual.
