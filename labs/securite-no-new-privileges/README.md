# no_new_privs

`USER` chooses a starting identity, not a permanent privilege ceiling.
Executing a root-owned setuid binary may change the effective UID.
Linux's `no_new_privs` prevents `execve` from granting new privileges, including
setuid and file-capability gains. The flag is inherited and cannot be unset.

For a neutral disposable Compose project `demo-reader`, add the security option
`no-new-privileges:true` and recreate the service. Compare `NoNewPrivs` in
`/proc/1/status` before and after. Dropping capabilities and choosing a non-root
UID are complementary controls, not substitutes for this flag.

The exercise builds a harmless C identity probe from pinned Alpine.
Compilation needs Alpine package access. No host compiler or setuid binary is
changed. Existing Docker settings are untouched.

See [the challenge](challenge/README.md).
