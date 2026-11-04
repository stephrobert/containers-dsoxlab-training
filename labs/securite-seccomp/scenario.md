# Narrow the engine profile, do not replace it

Your team's policy must reject `getpgid(2147483647)` with EPERM while allowing
`getpgid(0)` and `getpid`. The reserved PID argument targets only the harmless
probe, not runtime initialization. Without a filter, querying that nonexistent
PID returns ESRCH, not EPERM: the two errors differ, and only one proves the
filter bit. The supplied C probe performs these read-only calls and prints their
verdict.

**Start from the engine default profile, not from a blank one.** A profile whose
`defaultAction` is `SCMP_ACT_ALLOW` permits everything except the lines it
denies: that is a blacklist, not a policy, and it is never what a service should
carry. `assets/seccomp-defaut.json`, copied into the lab workspace, is the
reference profile. Derive it: take `getpgid` out of its blanket allow list, then
allow it back for every argument but the reserved one.

Two rules are needed, not one, and they must be mutually exclusive. An
`SCMP_ACT_ERRNO` on the reserved argument placed next to an unconditional
`SCMP_ACT_ALLOW` does not bite: the allow wins and the call reaches the kernel.
Use `SCMP_CMP_EQ` to deny and `SCMP_CMP_NE` to allow.

In `/opt/dsoxlab-securite-seccomp`, attach your derived profile to `worker` in
project `dsoxlab-securite-seccomp`. The starter explicitly uses `unconfined`.
Everything the default profile already refuses must stay refused, so add no
capability: `unshare` is only permitted there for containers holding
`CAP_SYS_ADMIN`.

The reference profile is a pinned copy from `moby/profiles` (`seccomp/v0.3.0`),
because the engine embeds its own in the binary: there is no file to copy off the
host. What you harden is therefore that copy, not the daemon's live profile.

Never change daemon defaults or run privileged containers.
