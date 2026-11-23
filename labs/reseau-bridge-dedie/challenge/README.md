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

## What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running. Three
containers are **already running**, and none was given a network option: they
are all on the default network.

```text
arriere   it LISTENS on port 8080 and answers a token
avant     it must be able to reach `arriere` BY NAME
tiers     the witness: it must NO LONGER reach `arriere`
```

There is **no form** to fill in in this lab. Everything is measured on the
state of the engine.

### 1. A network named `atelier`, with the subnet 172.28.5.0/24

The subnet is imposed, and that is not a whim: in production, a container
network has to coexist with everything else without collision, and that is
decided **at creation**.

A network created without declaring its subnet gets one the engine picks, which
is precisely what we want to avoid.

### 2. `avant` and `arriere` on that network, and no longer on the default one

**Two moves, not one.** That is the lab's trap, and it is a common one for
real: attaching a container to a network does not remove it from the other one.
A container can be on two networks at once.

And as long as it is, it stays reachable from the default network: the name will
resolve, the application will work, and the isolation you believe you have
obtained will not exist.

### 3. From `avant`, the name `arriere` resolves

That is the lesson, and what the default network refused. A dedicated network
carries a resolver that knows its members by name.

The check verifies **two** things: that the name does return `arriere`'s
address on `atelier`, and that the connection goes through. **Resolving is not
reaching**: a resolver can answer for an address no route reaches.

### 4. `tiers` no longer reaches `arriere`

That is the other half of the lesson: a dedicated network also **isolates**.

Notice that `tiers` does not move. It is not the one being changed, it is
`arriere` leaving the network they shared. At the start, `tiers` gets the token
with no trouble: it is your work that takes it away.

### Do not touch `tiers`

It is the witness. Destroying it or moving it would make this check pass
without proving anything, and the checks verify by name that it is still there,
on the default network and only that one.

### A word on tooling

`ping` is not a good tool here: ICMP depends on settings that have nothing to do
with the subject, and its failure would lead you to the wrong conclusion. A TCP
connection proves the same thing.

### What is not graded

The command you typed. The network can be created on the command line as well
as through the API, the attachment through a connect as well as by recreating
the container. Only the state counts.
