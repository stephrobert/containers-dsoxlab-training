# AppArmor

AppArmor adds path-based mandatory policy on top of Unix permissions. A
world-readable file can still be denied. A profile in `complain` mode logs
violations without enforcing them; `enforce` actually rejects access.

For a neutral disposable project `demo-notes`, compare the container's
`AppArmorProfile` from `docker inspect` with `/proc/1/attr/current`.
A rule such as `deny /notes/archive.txt r,` blocks reading that path even when
a broader `file,` rule allows file access.

The teaching profile is intentionally broad except for one denial. It is not
a production policy. Capabilities remain dropped and no host paths are mounted.
Setup requires AppArmor enabled and `apparmor_parser` already installed.
It refuses a preexisting profile with the reserved name, loads only its new
profile without cache writes, and leaves system configuration untouched.
No reboot persistence is claimed.

See [the challenge](challenge/README.md).
