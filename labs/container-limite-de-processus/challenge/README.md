# Brief

Work on `docker.lab`, in `/opt/dsoxlab-container-limite-de-processus`.

1. Keep one active `worker`, project `dsoxlab-container-limite-de-processus`,
   label `dsoxlab.lab=container-limite-de-processus`.
2. Set the container's pids limit to exactly 16; `pids.max` must agree.
3. Retain a positive memory cap no larger than 64 MiB and the CPU guard.
4. A finite burst must increment `pids.events`'s max counter while the worker
   survives without OOM.

The checker performs the guarded burst itself. Do not run an unbounded stressor.
