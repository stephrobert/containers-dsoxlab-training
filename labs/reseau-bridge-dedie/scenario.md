# Everybody talks to everybody

## The situation

You take over a server hosting a dozen containers: two business applications,
their databases, a metrics service, and three tools a former colleague had
installed "for testing".

None was given a network option. So they are all on the default network, and
that has two consequences you discover on the same day.

The first one is annoying: the applications have to talk to each other by IP
address, because names do not resolve. The addresses are written into the
configurations, and they change on the slightest restart.

The second one is considerably more serious: **the three test tools reach the
production databases**. Nobody wanted that, nobody forbade it. On a shared
network, everybody talks to everybody.

## The goal

Give the application a network of its own, and see that it fixes both problems
at once. Three containers are running, **all** on the default network:

```text
arriere   it LISTENS on port 8080 and answers a token
avant     it must be able to reach `arriere` BY NAME
tiers     the witness: it must NO LONGER reach `arriere`
```

Four things are expected:

1. A network named `atelier` exists, with the subnet **172.28.5.0/24**.
2. `avant` and `arriere` are attached to it, and they are **no longer** on the
   default network.
3. From `avant`, the **name** `arriere` resolves and returns its address on
   `atelier`.
4. `tiers`, left on the default network, **no longer reaches** `arriere`.

The brief is also written to `/opt/MISSION.md`.

## The trap, and it is a common one for real

**Attaching a container to a network does not remove it from the other one.** A
container can be on two networks at once, and it then keeps all of its
reachability from the default network.

That is the mistake that creates belief in an isolation that does not exist:
the name resolves, the application works, everything looks fine, and the test
tools still reach the database. So the second check requires **both** moves.

## Do not touch `tiers`

It is the witness. Destroying it or moving it would make the fourth check pass
without proving anything, and the checks verify by name that it is still there,
on the default network and only that one.

What has to change is `arriere`'s network, not the witness's.

## What is graded

The **state of the engine**, and nothing else. There is no form in this lab: a
network exists or it does not, a container is a member or it is not, a name
resolves or it does not, a connection succeeds or it does not.

One detail worth its place: the third check is not satisfied by a resolution
that succeeds, it also verifies that the connection goes through. **Resolving is
not reaching**: a resolver can perfectly well answer for an address no route
reaches.
