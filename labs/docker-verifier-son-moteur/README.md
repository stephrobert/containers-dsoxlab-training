# docker-verifier-son-moteur: four answers, not one

## What this lab tests

That "installed" and "usable" are two distinct states, and that the second one
is checked on four planes which are not repaired by the same action. It is the
first lab of the catalog, deliberately: before running a container, knowing
whether the engine can run one.

It is graded on the **state of the machine**, never on the commands typed.
`systemctl enable --now`, a hand-made repair of the unit link, `usermod -aG` or
`gpasswd -a` all reach the same states, and grading the command would grade a
style.

## Why four checks and not one

A successful `docker run` would prove all four at once. That is exactly what
must not be graded: it would hide **which one** was missing, and that is the
only piece of information useful to whoever is troubleshooting.

The case that justifies the split on its own is the second: a service started
by hand passes every test of the day and vanishes at the first reboot. There is
no way to tell that machine from a healthy one, except by looking at boot
activation separately.

## The starting state is broken, and that is the repo's rule

A test must bear on what the starting state does NOT carry. A setup that
installed and started Docker would make two checks green before any work: the
lab would be grading its own setup.

So the setup undoes three independent things:

| Undone | Check that measures it |
| --- | --- |
| `docker.service` stopped | 1, the engine answers |
| `docker.service` and `docker.socket` disabled | 2, persistence |
| the account removed from the `docker` group | 3, access without sudo |
| no container left behind | 4, an actual execution |

The socket deserves a mention: without stopping it **too**, systemd would
restart the service on first connection, and check 1 would go green without the
learner doing anything.

## Two traps laid on purpose

**Groups are read at login.** A learner who adds themselves to the `docker`
group then retries right away still gets a refusal, and believes they got the
action wrong. The check measures the declared membership, not what the current
session can do: the right action counts even if the terminal does not know it
yet. The brief says so in advance, because this trap discourages more than it
teaches.

**The command that adds a group can replace the others.** A check therefore
verifies the account keeps `sudo`. A learner who loses it did the action
sideways, and the machine becomes unadministrable, which is a worse failure
than the one being repaired.

## Why two checks go through `sudo`

So that the four planes stay independent. Querying the engine with the
learner's account would make "the engine answers" fail when only the group is
missing: two points lost for one forgotten action, and a message announcing a
mute daemon while it answers. Access without sudo has its own check, and only
that one measures it.

## What the lab does not require

Both units enabled. Either one is enough: the socket starting the service on
demand is a defensible answer, and requiring both would impose a route.
