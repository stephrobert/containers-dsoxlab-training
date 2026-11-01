# A non-root process can still acquire privileges

The worker starts as UID 1000, but its tiny `identity` executable is owned by
root with mode 4755. It only prints real and effective UIDs; it does not start a
shell or modify files. Without a privilege barrier, executing it gains EUID 0.

In `/opt/dsoxlab-securite-no-new-privileges`, keep that executable intact but
prevent elevation in the running service. Keep project
`dsoxlab-securite-no-new-privileges` and its lab label. The kernel flag and a
real execution must agree.

Do not modify host binaries, setuid policy or daemon configuration.
