# securite-rootless

**Audience:** learners.

Qualify the unprivileged daemon, its network and persistent data.

## What you will practice

Starting a Docker daemon without privileges: a **user** service carried by a
session-less system account, which means handing it its runtime directory and
its bus. That is the lab's only step, and the only one the checks ask of you.

The checks then build themselves a network, a volume and an HTTP service on
that engine to prove it really works. None of that is yours to build: be ready,
however, to explain UID mapping, the separate image store and the limits of
rootless networking, without confusing root inside the container with root on
the host.

## Safety boundaries

Only lab-labelled containers, volumes and files are changed. System-level exercises use dedicated lab accounts or restore the original daemon configuration.

## Validation

Tests inspect effective state on `docker.lab`; they do not award points for command history or file intent. Assertion messages are bilingual.
