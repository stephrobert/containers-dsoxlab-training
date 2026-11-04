# Scenario

A temporary audit account, `dsoxlab-auditor`, no longer needs its access to the
Docker daemon. That access is equivalent to root on this machine, since it grants
write access to the engine's socket.

## Mission

`dsoxlab-auditor` still exists, but **can no longer reach the daemon**.

Two checks measure this, and the second is the more demanding one: it does not
read a configuration line, it attempts a real call to the engine as that account.
A `docker ps` must fail there on a permission refusal.

The distinction matters, because **group membership is only one of the routes**
to the socket. Removing the account from the `docker` group without touching
anything else is enough here; but if another route remained, an ACL set on the
socket file for instance, the first check would be satisfied and the account
would keep its privilege. It is the access that is measured, not its
declaration.

If you use ACLs, note that `ls -l` still shows the `+` after a `setfacl -x`,
since the mask stays in place: only `getfacl` says what remains.

## Two prohibitions

- **Keep the account.** Deleting it does remove its access, by removing what the
  exercise asks you to keep: the audit account stays, only its privilege goes.
- **Do not change your own access.** Emptying the `docker` group of all its
  members would remove the audit account's access, and with it the access the
  work itself needs.

Both are verified before the measurements, and their message names the one you
crossed.
