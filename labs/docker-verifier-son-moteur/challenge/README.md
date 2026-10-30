# What is asked

On `docker.lab`, a throwaway Debian 13. Docker is **installed** there, and it is
not usable. Three things have been undone, and they are repaired by three
different actions.

The `lab-preuve:1.0` image is already on the machine: no registry access is
needed. Nothing here asks you to reinstall the package.

## 1. The engine answers

The daemon must be running. Not the client: the client already answers, and
that is what makes the failure misleading.

The check queries the engine itself rather than the systemd unit. A service
reported active whose daemon refuses connections would say "fixed" while
nothing is.

## 2. It will come back after a reboot

Starting a service and enabling it at boot are **two distinct actions**. Doing
only one leaves you a machine that works today and stops working on Monday.

On Debian, two units can carry that restart: the service, and the socket that
starts it on first connection. **Either one being enabled is enough**:
requiring both would impose a route, and several are defensible.

## 3. Your account talks to the engine without `sudo`

Access to the engine's socket is a matter of group membership. As long as your
account is not in it, every command needs `sudo`, which is no way to work.

**The trap, and it catches everyone once**: groups are read at login. After
adding yourself, your current session does not know it yet, and the command
still fails. It is not that the action failed, it is that it does not apply to
a session already open. Reconnect to see it. The check looks at the membership.

Be careful **not to replace** your other groups while adding this one: a check
verifies the account keeps `sudo`, because an account that lost it can no
longer administer anything, and it is a common mistake with the command used
here.

## 4. A container has actually been executed

A daemon can answer and still be unable to run anything: broken storage
driver, missing cgroups, unreadable image. Only an execution proves it.

Run a container from `lab-preuve:1.0` and **leave it there**: that is the
proof. Its exit status does not matter, and this image stops by itself right
away. The check looks for a container, alive or exited, from that image.

## What is not graded

The command you typed. Each of these four states can be reached several ways,
and they all count the same.
