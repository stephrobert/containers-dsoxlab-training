# seccomp

Seccomp filters syscall numbers and arguments, not filesystem paths.
Docker normally applies a default filter. `seccomp:unconfined` removes that
protection from a container; it does not change the daemon's policy.

A neutral project `demo-counter` can attach a JSON profile through Compose's
`security_opt`. `SCMP_ACT_ERRNO` rejects a call with an errno instead of killing
the process. `errnoRet: 1` selects EPERM. A `defaultAction` of
`SCMP_ACT_ALLOW` is useful for one controlled teaching denial, but is not a
production allowlist.

Filters take effect during OCI runtime initialization, before the application
starts. Blocking `getppid` globally can therefore break runc itself.
An argument rule (`index: 0`, `op: SCMP_CMP_EQ`) restricts this exercise's denial
to `getpgid(2147483647)`, leaving normal process queries available.

Recreate the service after changing the filter. `Seccomp: 2` in
`/proc/1/status` proves filtering is active, not that the intended call is
blocked. A syscall probe provides the second half of the proof.

The exercise builds its harmless probe using Alpine packages; network access is
needed for compilation. See [the challenge](challenge/README.md).
