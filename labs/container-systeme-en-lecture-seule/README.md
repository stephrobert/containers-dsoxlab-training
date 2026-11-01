# Read-only root, writable runtime

Compose's `read_only` protects the container's root filesystem. It does not
automatically make separate mounts read-only, and it is not a backup mechanism.
Applications often still need PID files, temporary files or sockets.

For a neutral project `demo-agent`, identify its actual writable paths before
enabling read-only root. A bounded tmpfs can supply one runtime directory:
`/var/run:rw,noexec,nosuid,size=2m` is an example, not this challenge's contract.
Tmpfs data disappears with the container and counts toward its memory cgroup.
Noexec forbids direct execution from that mount; it does not prevent an
interpreter from reading a script.

Compare `HostConfig.ReadonlyRootfs`, mount type, `df` capacity and an actual
write attempt. Do not accept a silent application that no longer updates its
runtime files.

See [the challenge](challenge/README.md). Existing engine configuration is
preserved; no host filesystem is remounted.
