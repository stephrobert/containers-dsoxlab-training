# securite-socket-proxy

**Audience:** learners.

Limit the loopback proxy to two read-only API endpoints.

## What you will practice

GET /_ping and GET /version succeed; other paths and mutating methods are denied.

## Safety boundaries

Only lab-labelled containers, volumes and files are changed. System-level exercises use dedicated lab accounts or restore the original daemon configuration. Disk pressure is simulated by a bounded 16 MiB volume and never fills the host filesystem.

## Validation

Tests inspect effective state on `docker.lab`; they do not award points for command history or file intent. Assertion messages are bilingual.
