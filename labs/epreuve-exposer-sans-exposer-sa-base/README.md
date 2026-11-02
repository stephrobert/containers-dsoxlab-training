# epreuve-exposer-sans-exposer-sa-base: the "Expose and connect" module's test

## What this test measures

Making two containers talk to each other by name, and opening to the outside
only what has to be open. It closes the module's lessons and re-explains
nothing: what you need to know was taught there, this measures it.

Its `lab_type: challenge` is what allows its `exam_passing_score`, set to **75**.
The five checks are of equal weight, and one of them is critical.

## The fault that was planted, stated nowhere in the brief

| Fault | Visible symptom | What it teaches |
| --- | --- | --- |
| both containers on the **default** network | no name resolves, although the addresses do reach each other | the default network gives a route, not a resolver |
| the shop window queries `stock`, which nobody carries | the expected name does not resolve, even on a network of its own | that is what network aliases are for |
| `inventaire` publishes a port on every interface | the audit reports it | nothing removes a `-p` from an existing container |
| `vitrine` publishes on every interface | the audit reports it too | a publication binds to an address, not only to a port |

All four are independent, and they are exactly the ones you commit when
starting two containers by hand without thinking about the network. The first is
the most instructive: it "works" by IP address, so the network is not suspected.

## Four symptoms, two moves

Create a network of your own, then recreate both containers on it: one with its
alias and no publication, the other published on the one interface that is
asked for. **Two moves settle all four faults**, and that is what makes the test
worth taking: diagnosis comes before action.

Fixing fault by fault works too, in four moves. The tests grade the final state,
so both paths earn the same mark.

## Why the real name is required as well as the queried one

Without that requirement, renaming the container to `stock` would satisfy the
other checks, and the learner would have learned nothing about aliases. It is
**stated in the brief**, so it is not a trap, and it describes the real
situation: the application has its own name, written in a configuration you
cannot change, and operations keeps theirs, the one in the logs and the
inventories.

Measured in this repository: an alias set on a network leaves the real name
resolving. Both requirements can therefore be met together, and only a rename
puts them in conflict.

## The critical requirement

**A port published on the inventory fails the test**, even at 80 points. A
database reachable from the company network is the fault this test exists to
eliminate: making up for it with good marks elsewhere would mean issuing a
certificate on an exposed installation.

## Where the witness value lives, and why in the image

The value only the inventory holds is carried by an **image label**, not by a
file on the host and not by a volume. Two reasons:

- the test asks for the containers to be **recreated**, and a value carried by
  the image survives that: the traversal check therefore does not punish the
  right way of going about it;
- volumes are not on this module's syllabus. Introducing them here would add a
  notion the learner has not seen.

It is **drawn at random on every run**: a number frozen into a public repository
is a published answer.

## What the test does not measure

The network's name, and the path taken. It grades the final state. A learner who
names their network differently, or who takes four moves, has fixed the fault.

## After the test

`dsoxlab clean` removes everything the lab set up, **including the network you
created**: it is found through the lab's containers attached to it, since the
test imposes no name. The engine's default network is never touched.
