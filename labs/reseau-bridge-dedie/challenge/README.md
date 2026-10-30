# What is asked

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

## 1. A network named `atelier`, with the subnet 172.28.5.0/24

The subnet is imposed, and that is not a whim: in production, a container
network has to coexist with everything else without collision, and that is
decided **at creation**.

A network created without declaring its subnet gets one the engine picks, which
is precisely what we want to avoid.

## 2. `avant` and `arriere` on that network, and no longer on the default one

**Two moves, not one.** That is the lab's trap, and it is a common one for
real: attaching a container to a network does not remove it from the other one.
A container can be on two networks at once.

And as long as it is, it stays reachable from the default network: the name will
resolve, the application will work, and the isolation you believe you have
obtained will not exist.

## 3. From `avant`, the name `arriere` resolves

That is the lesson, and what the default network refused. A dedicated network
carries a resolver that knows its members by name.

The check verifies **two** things: that the name does return `arriere`'s
address on `atelier`, and that the connection goes through. **Resolving is not
reaching**: a resolver can answer for an address no route reaches.

## 4. `tiers` no longer reaches `arriere`

That is the other half of the lesson: a dedicated network also **isolates**.

Notice that `tiers` does not move. It is not the one being changed, it is
`arriere` leaving the network they shared. At the start, `tiers` gets the token
with no trouble: it is your work that takes it away.

## Do not touch `tiers`

It is the witness. Destroying it or moving it would make this check pass
without proving anything, and the checks verify by name that it is still there,
on the default network and only that one.

## A word on tooling

`ping` is not a good tool here: ICMP depends on settings that have nothing to do
with the subject, and its failure would lead you to the wrong conclusion. A TCP
connection proves the same thing.

## What is not graded

The command you typed. The network can be created on the command line as well
as through the API, the attachment through a connect as well as by recreating
the container. Only the state counts.
