# "Docker is installed", and still nothing works

## The situation

You take over a build machine a colleague set up before leaving. Their last
message reads: "Docker is installed, you can run your containers."

The package is indeed there. `docker` answers when you type its name. And yet
none of your commands get through: one talks about permission denied, another
about an unreachable daemon, and you cannot tell whether a right is missing, a
service, or both.

This is the most ordinary situation that follows a package installation, and
also the one where most time is lost: people reinstall, hunt for a network
problem, suspect the image. The package has nothing to do with it. "Installed"
and "usable" are two different states, and the second one is checked on
several planes that are not repaired by the same action.

## The goal

Make this engine genuinely usable, and prove it by something other than "works
on my machine".

Four things are checked, and they are **independent**:

1. the engine answers;
2. it will come back on its own after the machine reboots;
3. your account talks to it **without** `sudo`;
4. a container has actually been executed.

The full brief also sits on the machine, in `/opt/MISSION.md`.

The `lab-preuve:1.0` image is already present: no registry access is needed,
and nothing in this mission asks you to reinstall the package.

## What is graded

The **state of the system**, never the commands typed. The service, its
activation at boot, your account's membership of the group that opens the
socket, and the trace of a container having run. Two learners reaching the same
state by two different routes have both succeeded.

One point is worth knowing in advance, because it looks like a failure: an
account's groups are read **at login**. Adding yourself to a group changes
nothing for the session already open, and you have to reconnect for your shell
to benefit. The check looks at the membership, not at your shell: the right
action counts even if your current terminal does not know it yet.
