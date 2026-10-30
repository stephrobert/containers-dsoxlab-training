# reseau-diagnostic-dns: the networking track's assessment

## What this assessment tests

Diagnosis, not a command. It closes the five networking labs of the course and
explains nothing again: what is needed was taught there, this one measures it.

It is the section's only `lab_type: challenge`, and that is what allows its
`exam_passing_score`, set to **75**: three checks out of four.

## The fault that is set, and it is stated nowhere in the brief

| Fault | Visible symptom | What it teaches |
| --- | --- | --- |
| both containers on two **different** dedicated networks | no name resolves | two stacks deployed separately do not talk |
| the application looks for `base`, the container is called `catalogue` | the expected name does not resolve, even on a shared network | network aliases exist for this |
| `catalogue` publishes a port on all interfaces | the audit reports it | nothing removes a `-p` on an existing container |

All three are independent and all credible. The first is the ordinary case of
two teams deploying on their own, which the scenario tells.

## Three symptoms, one correction

Recreate `catalogue` on `boutique`'s network, with the alias and without
publication. **A single move fixes all three faults**, and that is what makes
the assessment worth something: the diagnosis comes before the hand.

Fixing them one at a time works too, in three goes. The tests grade the state,
never the path, so both count. But one teaches diagnosis and the other teaches
poking around.

## Why the fourth check requires the real name

Without it, **renaming the container to `base` would satisfy the other three**,
and the learner would have learned nothing about network aliases.

The requirement is in the brief, so it is not a trap. And it is the real
situation: the application has its own name, written in a configuration that
cannot be changed, and operations keeps theirs, the one in the logs and the
inventories. **An alias is added, it does not replace.**

Measured on `docker.lab` on 2026-10-30: an alias set on a network leaves the
real name resolving. So both requirements can be satisfied together, and only a
rename sets them against each other.

## What the checks' messages say, and do not say

A lab guides: its message names the missing move. **A challenge assesses: its
message names the precise symptom and stops there.**

No message in this file says "attach the container" or "set an alias". The hints
are there for that, and they cost points. It is the only difference in writing
between a lab and a challenge in this repository, and it is a whole one.

## Why resolving and reaching are two checks

Their causes differ. A resolver can answer for an address no route reaches, which
happens as soon as a container is on several networks.

Separating them lets the message name the right fault. Merged, they would say
"it does not work", which is exactly what a learner already knows on arrival.

## Why the first check verifies the address is the right one

It is not satisfied by a resolution that succeeds: it verifies that the returned
address is one `catalogue` actually carries.

A name pointing elsewhere is **worse** than no name at all: the application
would talk to something else, and the symptom would become
incomprehensible. That is a real case as soon as a name lingers in a resolver.

## The cleanup clears more than the setup laid down

A diagnosis assessment leaves behind what the learner built while searching: an
extra network, a stopgap container. The setup's two networks are named, but a
network created by the learner cannot be, hence the final `network prune`.

It touches neither the engine's networks nor those still carrying a container:
so it cannot break another lab of the catalogue, each removing its own
containers in its own cleanup.

## The starting state is broken, and that is the repository's rule

All four checks are false at the start. A setup task **verifies** the three
faults before handing over: neither name resolves from `boutique`, and the port
is indeed published.

## What the assessment does not require

A path. Recreating the container, attaching then detaching it, creating a third
network: anything leading to the required state counts. The tests name no
network, and they read the container's addresses on **all** of its networks.
