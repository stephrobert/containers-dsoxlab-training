# reseau-publication-de-ports: three postures, one default

## What this lab tests

That publishing a port is a **three**-way choice, and that its default is the
most open of the three. `-p 8080:80` publishes on all interfaces, because the
publication address is optional. It is the most ordinary move in Docker, and the
one that exposes a service without anyone deciding to.

## The three postures, measured before being written

On `docker.lab`, on 2026-10-30:

| Publication | from `127.0.0.1` | from the routable address |
| --- | --- | --- |
| `-p 127.0.0.1:P:80` | reaches | **does not reach** |
| `-p <routable>:P:80` | **does not reach** | reaches |
| none | does not reach | does not reach |

Those three lines are the lab. Each matches a real need, and each goes wrong
differently.

## The trap that would invalidate every one of these checks

Docker's proxy **accepts a connection before anything is listening**. Verified
here on 2026-10-30, on a `-p 127.0.0.1:18099:1234` whose container was listening
nowhere: the connection succeeded.

So the checks read the **answer**, never the connection alone. A test satisfied
by a successful `connect()` would declare an absent service reachable, and this
lab would grade exactly the opposite of what it measures.

That is also why the listener answers a token rather than merely existing: a
readable answer is the only proof that a service serves.

## Why each posture is measured twice

The checks read what the engine **declares** it publishes, then test what the
machine actually **does**.

The two can diverge: a firewall rule, a second container published on the same
port, a listener that did not come back up. A lab reading only the declaration
would validate a container recreated without its service.

## Why an image rather than a command

Changing a container's publication requires **recreating** it: `-p` cannot be
changed on a running container, and that is one of the lab's lessons.

So the learner must be able to relaunch the listener without rewriting it, hence
the image carrying it in `CMD`. A lab that had passed the listener on the
command line would have forced the learner to guess a command they have never
seen, which has nothing to do with the subject.

## No address is hardcoded

Not in the tests, not in the solution, not in the setup. The routable address is
derived from the default route, at grading time.

A test carrying `10.10.120.11` would be wrong on a machine addressed
differently, and the lab would die at the first network change. The setup does
write it into the brief, though, since the learner has to put it in their `-p`.

## Two inseparable assertions, and why they make one check

The fourth check requires that `interne` publishes nothing **and** that it stays
reachable by `vitrine`.

The two do not separate: publishing nothing is trivial by destroying the
container. A check satisfied by removing the subject measures nothing, so the
internal reachability is the compulsory counterpart.

## The starting state is broken, and that is the repository's rule

| Container | Starting state | Expected move |
| --- | --- | --- |
| `vitrine` | `0.0.0.0:18080` | republish on `127.0.0.1` alone |
| `annexe` | publishes nothing | publish on the routable address alone |
| `interne` | `0.0.0.0:18082` | publish nothing at all |

None of the three mistakes is an accident: each is the error made by default. A
setup task **verifies** that state before handing over.

## What the lab does not require

A path. The containers can be recreated on the command line as well as through
the API or a Compose file. Only the state counts, and it is measured on the
engine and on the network.
