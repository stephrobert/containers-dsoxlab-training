# reseau-bridge-dedie: naming and isolating

## What this lab tests

That a dedicated network brings **two** things, not one: name resolution among
its members, and isolation of those that are not in it. The previous lab had
the learner observe the absence of DNS on the default network; this one has
them fix the situation and measures both effects.

## No form here, and that is deliberate

The two previous labs had answers written down. This one has things **built**.
The four checks read the state of the engine, not a file.

That is a progression decision, not a change of style: after two labs of
observation, the learner has to make moves, and a third form in a row would
mostly teach weariness.

## The starting state is reachable, and that is the delicate point

At the start, all three containers are on the default network, so `tiers`
**does** reach `arriere`: the isolation check is **false** before any work,
which `valider-labs.py` requires.

A setup that had already separated the containers would make that check true
with no work, and it would no longer be a test but an assumption of the setup.
That is the repository's most often broken rule, and it is particularly easy to
break on an isolation lab, where the healthy state looks like an empty one.

Measured on `docker.lab` on 2026-10-30:

| Moment | `tiers` reaches `arriere` | `avant` resolves `arriere` |
| --- | --- | --- |
| at the start | yes, it gets the token | no |
| after the work | no | yes, to its address on `atelier` |

## The lab's trap, and it is a common one for real

Attaching a container to a network **does not remove it** from the other one. A
container on two networks keeps all of its reachability from the default
network.

That is the mistake that creates belief in an isolation that does not exist:
the name resolves, the application works, everything looks fine. So the second
check requires both moves, and its message names the one that is missing
instead of saying "not attached".

## Why the witness is protected

The fourth check would also be true if `tiers` or `arriere` disappeared: there
would be nobody left to fail to reach. **A check satisfied by removing the
subject measures nothing.**

Two guards hold it: a shared precondition verifies that all three containers
are running, and the fourth check verifies that `tiers` is on the default
network **and only that one**. The third check also proves that `arriere` is
alive and answering.

## Why the subnet is imposed

Because that is the real move. In production, a container network has to
coexist with everything else without collision, and that is decided at
creation. A network created without `--subnet` gets a plan the engine picks,
which is precisely what we want to avoid.

## Resolving is not reaching

The third check is not satisfied by a resolution that succeeds. It verifies
that the name does return the container's address **on this network**, and then
that the connection goes through.

A resolver can answer for an address no route reaches, and that is a case met
for real as soon as a container is on several networks. Two assertions beat one
hasty conclusion.

## A cleanup trap, paid for in advance

A network whose containers are still members **cannot be removed**: `docker
network rm` refuses with "has active endpoints". So the containers go first, the
network second.

That is exactly the kind of dependency a cleanup written the wrong way round
reveals on the first `dsoxlab reset`, in a message that does not state the
cause.

And the `atelier` network is removed **even though the learner created it**:
without that, three checks out of four would be true on the next pass before any
work.

## What the lab does not require

A path. The network can be created through `docker network create` as well as
through the API; the attachment through `docker network connect` as well as by
recreating the container with `--network`; the resolution can be observed
through `nslookup`, `getent` or a plain connection.
