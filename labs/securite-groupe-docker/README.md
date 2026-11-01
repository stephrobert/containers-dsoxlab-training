# securite-groupe-docker

**Audience:** learners.

Remove only docker-group membership from the synthetic audit account.

## What you will practice

dsoxlab-auditor remains present but is no longer a member of docker.

## Safety boundaries

Only lab-labelled containers, volumes and files are changed. System-level exercises use dedicated lab accounts or restore the original daemon configuration. Disk pressure is simulated by a bounded 16 MiB volume and never fills the host filesystem.

## Validation

Tests inspect effective state on `docker.lab`; they do not award points for command history or file intent. Assertion messages are bilingual.
