# epreuve-exposer-sans-exposer-sa-base: the "Expose and connect" module's test

## What this test measures

Exposing an application without exposing what it holds. It closes the module's
lessons and explains nothing anew: what you need was taught there, this one
measures it.

Its `lab_type: challenge` is what allows its `exam_passing_score`, set to
**75**. The five checks carry equal weight, and one of them is critical.

## Why it was refocused

It restated an earlier lesson's lab: four of its five checks were about name
resolution, while the module's third teaching, **isolation**, was measured
nowhere in the catalog.

An end-of-module test grades the **combination** of what the module teaches,
not what an earlier lesson has already proven.

## The three teachings, and the combination

| Check | What it measures |
| --- | --- |
| the front end publishes on the requested interface only | a publication binds to an **address** as much as to a port |
| the database answers to an **alias** distinct from its name | a service name survives the container's replacement, a rename does not |
| the database sits on a network with **no way out** | what lives there resolves names and no longer gets out |
| the database publishes no port | **the critical requirement** |
| the business request succeeds **despite** the isolation | the combination, and it is what this test exists for |

The first two requirements work against the third: isolating the database cuts
it off from everything, while publishing the front end calls for a way out.
Holding both takes putting the front end on **both** networks, which no check
says.

## How isolation is proven, and why not otherwise

Two facts, and only the second is proof. All of the database's networks are
declared **internal**, and above all the database has **no default route**,
which is read inside the container.

We do **not** attempt a connection to the outside. Measured on 2026-11-02: a
container on an internal network has no default route, where an ordinary
container has one. An attempted connection would instead pass on a machine with
no outbound access, so for the wrong reason, and would keep passing the day the
isolation disappeared.

Also measured, and without which the test would be unplayable: a container
attached to **both** networks keeps its default route **and** resolves the
alias.

## The critical requirement

**A published port on the inventory fails the test**, even at 80 points. A
database reachable from the company network is the fault this test exists to
eliminate: offsetting it with good points elsewhere would mean issuing a
certificate on an exposed installation.

It is about **that single fact**. It used to mix two, the published port and the
network attachment, so a learner who got the network wrong lost their critical
requirement for a reason the brief does not announce.

## Where the witness value lives, and why in the image

The value only the inventory holds is carried by an **image label**, not by a
host file nor by a volume. Two reasons:

- the test asks you to **recreate** the containers, and a value carried by the
  image survives their recreation: the traversal check therefore does not
  punish the right way of going about it;
- volumes are not in this module's syllabus. Introducing them here would add a
  notion the learner has not seen.

It is **drawn at random on every run**: a number frozen into a public
repository is a published answer.

## What the test does not measure

Network names, and the path taken. It grades the final state. A learner who
names their networks otherwise, or who proceeds in several steps, has fixed the
outage.

## After the test

`dsoxlab clean` removes everything the lab put in place, **including the
networks you created**: they are found through the lab's containers attached to
them, since the test imposes no name. The engine's default network is never
touched.
