# An audit account that no longer needs the engine

## The situation

On `docker.lab`, the temporary audit account `dsoxlab-auditor` can still reach
the Docker daemon. That access is equivalent to root on the machine, and its
assignment is over.

## Mission

`dsoxlab-auditor` still exists, but **can no longer reach the daemon**. A
`docker ps` run as that account must fail on a permission refusal.

Two prohibitions:

- **Keep the account**, and the rest of its rights.
- **Do not change your own access**: the `docker` group keeps its other members.

## What is graded

1. The account is no longer a member of the `docker` group.
2. A real call to the engine, as that account, is refused. Group membership is
   only one route to the socket: an ACL set on its file would leave the
   privilege. `getfacl` shows what remains; `ls -l` still displays the `+` after
   a `setfacl -x`, since the mask stays in place.

Crossing a prohibition makes both checks fail, and the message names it.
