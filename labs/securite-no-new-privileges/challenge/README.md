# A program that hands root to an ordinary account

## The situation

On `docker.lab`, the `worker` of project `dsoxlab-securite-no-new-privileges`
starts under UID 1000. Its image contains `/usr/local/bin/identity`, a setuid root
program that displays the real UID and the effective UID. Run by the worker, it
displays `1000:0`: it obtained root. The project is in
`/opt/dsoxlab-securite-no-new-privileges`.

## Mission

Prevent this gain in the service, without touching the program:

1. the barrier is declared on the container;
2. PID 1 reports `NoNewPrivs: 1`;
3. `identity`, run under UID and GID 1000, displays `1000:1000`.

The program keeps its root owner and mode 4755. Keep the project, the
`dsoxlab.lab=securite-no-new-privileges` label and the resource limits. Change
neither the host nor the daemon.
