# reseau-interne: two isolations that are not alike

## What this lab tests

That there are **two** isolations, confused because both are called
"isolating":

| Posture | What it gives | What for |
| --- | --- | --- |
| no network | no interface, no neighbour, no way out | a job that needs nobody |
| internal network | members talk by name, and do not get out | a database only its application must reach |

Taking one for the other gives either an unusable service or an exposed one. The
lab has both obtained on the same machine, so that the difference is seen rather
than asserted.

## Measured before being written

On `docker.lab`, on 2026-10-30:

| Posture | interfaces besides loopback | reaches the witness | neighbour by name |
| --- | --- | --- | --- |
| default network | 1 | yes | no |
| no network | 0 | no | not applicable |
| internal network | 1 | no | yes |

And one detail that says everything about the mechanism: a container on an
internal network has **no default route**. The isolation is not a filter placed
in front of it, it is the absence of the path. The reference solution checks that
explicitly, because it is the clearest way to understand what is going on.

## How "getting out" is measured, and why not against the internet

Against a witness published on the machine's routable address.

A lab depending on outbound access would fail on an isolated machine, and its
message would speak of successful isolation when there is no network at all: **it
would grade the opposite of what it measures**. The local witness removes that
dependency, and it makes the measurement reproducible.

## Why the first two checks are separate

The first reads the interfaces **inside** the container. The second tests what it
**can reach**.

That is not a repetition: a container may have lost its interface and still share
a network stack with another one, in which case it still reaches. Reading the
configuration and testing the behaviour are two measurements, and separating them
is what lets the message name the right cause.

## Why the first check looks at the effect, not the path

It requires that no interface remains besides the loopback, not that the
container declares a particular network.

Recreating it with the option that deprives it of a network is the plain move,
and the one the lab teaches. Detaching the container from its networks gives the
same result. Both count, because the repository's rule is to grade the state,
never the command.

## The fourth check is indivisible

It requires three things at once: both containers on the confined network, the
neighbour reached **by name**, and no way out.

They do not separate. Confining without the members talking to each other would
give an unusable service; having them talk without confining them would be just
one more dedicated network, which is the previous lab. The conjunction is the
skill.

## Why the witness is protected

Checks 2 and 4 would also be true if `dehors` disappeared: there would be nothing
left to not reach.

So a precondition verifies that it is running **and** that it answers from the
host. If its publication has been changed, the isolation checks would pass for
the wrong reason, and the message says so rather than letting success be
believed.

## The starting state is broken, and that is the repository's rule

The three containers to isolate are on the default network, so all four checks
are false. A setup task **verifies** that `coffre` and `atelier-b` do reach the
witness before handing over: without it, two checks would be true before any
work.

## A cleanup trap, paid for in advance

Two ordering dependencies, not one. A network whose containers are still members
cannot be removed, and neither can an image containers derive from. So the
containers go first, the network and the image second.

## What the lab does not require

A path. The network can be created on the command line as well as through the
API; the containers can be placed on the right network at creation as well as
through an attach followed by a detach.
