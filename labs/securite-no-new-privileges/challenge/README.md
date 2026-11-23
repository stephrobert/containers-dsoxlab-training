# A non-root process can still acquire privileges

The worker starts as UID 1000, but its tiny `identity` executable is owned by
root with mode 4755. It only prints real and effective UIDs; it does not start a
shell or modify files. Without a privilege barrier, executing it gains EUID 0.

In `/opt/dsoxlab-securite-no-new-privileges`, keep that executable intact but
prevent elevation in the running service. Keep project
`dsoxlab-securite-no-new-privileges` and its lab label. The kernel flag and a
real execution must agree.

Do not modify host binaries, setuid policy or daemon configuration.

## Brief

Work on `docker.lab`, in `/opt/dsoxlab-securite-no-new-privileges`.

1. Keep `worker` running in project `dsoxlab-securite-no-new-privileges`,
   with label `dsoxlab.lab=securite-no-new-privileges`.
2. Enable no-new-privileges at runtime; PID 1 must report `NoNewPrivs: 1`.
3. Preserve `/usr/local/bin/identity`, owned by UID 0 with mode 4755.
4. Executing that binary as UID/GID 1000 must report `1000:1000`, not `1000:0`.

Do not replace the binary, change its mode or alter the host's setuid policy.
Preserve the bounded resource settings.
