# Brief

Work on `docker.lab`, in `/opt/dsoxlab-securite-seccomp`.

1. Keep one active `worker`, project `dsoxlab-securite-seccomp`,
   label `dsoxlab.lab=securite-seccomp`.
2. Attach an explicit JSON seccomp profile, not `unconfined`.
3. PID 1 must report filtering mode 2.
4. The existing `/usr/local/bin/syscall-probe` must observe
   `getpgid(sentinel)=EPERM getpgid(0)=allowed getpid=allowed`.
   The sentinel argument is 2147483647; do not block ordinary runtime calls.
5. **Derive `seccomp-defaut.json`, the engine default profile shipped with the
   lab**, rather than writing a new one. Everything that profile already
   refuses must stay refused: the check runs `unshare -U` inside the container,
   and it must fail. Add no capability.

A profile whose `defaultAction` is `SCMP_ACT_ALLOW` permits everything except
the lines it denies: that is a blacklist, and never what a service should carry.

Keep the supplied probe and resource caps. Do not change the daemon.
