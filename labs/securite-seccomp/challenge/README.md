# Narrow the engine profile, do not replace it

## The situation

On `docker.lab`, the `worker` of project `dsoxlab-securite-seccomp` runs without a
filter (`unconfined`). Your team wants to refuse it a single call,
`getpgid(2147483647)`, and nothing else. That process identifier does not exist:
without a filter, the call returns ESRCH; refused, it returns EPERM.

The project is in `/opt/dsoxlab-securite-seccomp`. It contains
`seccomp-defaut.json`, a pinned copy of Docker's default profile
(`moby/profiles`, `seccomp/v0.3.0`): the engine embeds its own in its binary,
there is no file to copy off the host.

## Mission

1. Attach a JSON profile to `worker`, not `unconfined`.
2. PID 1 reports filtering mode 2.
3. `/usr/local/bin/syscall-probe`, already in the image, displays
   `getpgid(sentinel)=EPERM getpgid(0)=allowed getpid=allowed`.
4. **The profile derives from `seccomp-defaut.json`.** Everything that profile
   refuses stays refused: the check runs `unshare -U` in the container, which must
   fail.

The default profile allows `getpgid` without condition. A refusal added next to
that permission does not bite: the two cases must not overlap. A profile whose
`defaultAction` is `SCMP_ACT_ALLOW` does not fit, because it permits everything
but what it mentions.

Keep the project, the `dsoxlab.lab=securite-seccomp` label, the probe and the
resource limits. Add no capability, do not use `privileged` and do not change the
daemon.
