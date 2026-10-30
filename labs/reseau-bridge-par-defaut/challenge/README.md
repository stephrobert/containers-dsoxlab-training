# What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running. Two containers
are **already running**, and neither was given a network option: they are
therefore on the default network, the one used without being chosen.

```text
arriere   it LISTENS on port 8080 and answers a token
avant     it does nothing, it is your observation post
```

The first three answers go into `/opt/lab-reseau/reponses.txt`, one line per
entry, with no spaces around the equals sign.

## 1. The address of `arriere`

On the `adresse=` line.

On this network, the address is the **only** way to designate another
container. It is also what makes it unusable in production: an address is
reassigned at every creation.

## 2. The gateway of the default network

On the `passerelle=` line.

It is read by inspecting the **network**, not a container. The distinction
matters: a container knows its own address, the network knows its gateway.

Everything goes out through it, and it is also the address a container uses to
reach a service on the host.

## 3. The host interface that carries that gateway

On the `interface=` line.

This is the check that connects the two worlds. The gateway the containers see
is an address carried by a **real** interface of the host, a bridge the engine
created at startup.

Look on the host's side, not the containers'. An answer of the form
`docker0@if3` is accepted.

## 4. The token, obtained by a real connection

From the container `avant`, reach `arriere` and put the token it answers into
`/jeton.txt`, **inside `avant`**.

The token is nowhere else: not in `arriere`'s logs, not in any file. It can
only be obtained by opening a connection, and it is drawn at random on every
pass.

The file is expected **inside `avant`**, not on the host: that is where the
state matters.

## The warning that will save you time

On this network, a container's **name** does not resolve. Try it, see it, and
look for why: that is the lesson of the lab, and the next lab answers it.

`ping` is not a good tool here: ICMP depends on settings that have nothing to
do with the subject. A TCP connection proves the same thing.

## What is not graded

The command you typed, nor the path you took. The three values are recomputed
by questioning the engine, then compared with what you wrote. Several paths give
the same answer, and all of them count.
