# It worked in development, and now the name does not resolve

## The situation

Your application runs as two containers: a front end and a database. On the
developer's machine everything works, because they wrote the database's IP
address into the configuration and read it once and for all.

The server reboots. The containers are recreated, the addresses change, and the
application no longer finds its database. You replace the address with the
container's name, which looks like the right idea, and you get:

```text
nc: bad address 'arriere'
```

The name does not resolve. Not "badly", not "slowly": not at all. And yet the
two containers reach each other perfectly well by address.

This is not a failure, this is the default network. The one nobody chooses,
because it is where you land when you say nothing.

## The goal

Map that network before leaving it. Two containers are running, neither was
given a network option:

```text
arriere   it LISTENS on port 8080 and answers a token
avant     it does nothing, it is your observation post
```

Fill in the three lines of `/opt/lab-reseau/reponses.txt`:

```text
adresse=<the IP address of arriere>
passerelle=<the gateway of the default network>
interface=<the name of the HOST interface that carries that gateway>
```

Then, **from the container `avant`**, reach `arriere` and put the token it
answers into a file, **inside `avant`**:

```text
/jeton.txt
```

The token is nowhere else: not in `arriere`'s logs, not in any file. It can
only be obtained by opening a connection, and it is drawn at random on every
pass.

The brief is also written to `/opt/MISSION.md`.

## What is graded

The **state of the system**, never the commands you typed. The three answers
are recomputed at grading time by questioning the engine.

The third question is the one that connects the two worlds: the gateway the
containers see is an address carried by a **real** interface of the host. Until
you have seen it, container networking stays an abstraction.

And one thing better known than discovered: **the host reaches the containers
of this network directly**, with no published port involved. That is handy for
debugging, and it is a security subject in its own right.

## What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running. Two containers
are **already running**, and neither was given a network option: they are
therefore on the default network, the one used without being chosen.

```text
arriere   it LISTENS on port 8080 and answers a token
avant     it does nothing, it is your observation post
```

The first three answers go into `/opt/lab-reseau/reponses.txt`, one line per
entry, with no spaces around the equals sign.

### 1. The address of `arriere`

On the `adresse=` line.

On this network, the address is the **only** way to designate another
container. It is also what makes it unusable in production: an address is
reassigned at every creation.

### 2. The gateway of the default network

On the `passerelle=` line.

It is read by inspecting the **network**, not a container. The distinction
matters: a container knows its own address, the network knows its gateway.

Everything goes out through it, and it is also the address a container uses to
reach a service on the host.

### 3. The host interface that carries that gateway

On the `interface=` line.

This is the check that connects the two worlds. The gateway the containers see
is an address carried by a **real** interface of the host, a bridge the engine
created at startup.

Look on the host's side, not the containers'. An answer of the form
`docker0@if3` is accepted.

### 4. The token, obtained by a real connection

From the container `avant`, reach `arriere` and put the token it answers into
`/jeton.txt`, **inside `avant`**.

The token is nowhere else: not in `arriere`'s logs, not in any file. It can
only be obtained by opening a connection, and it is drawn at random on every
pass.

The file is expected **inside `avant`**, not on the host: that is where the
state matters.

### The warning that will save you time

On this network, a container's **name** does not resolve. Try it, see it, and
look for why: that is the lesson of the lab, and the next lab answers it.

`ping` is not a good tool here: ICMP depends on settings that have nothing to
do with the subject. A TCP connection proves the same thing.

### What is not graded

The command you typed, nor the path you took. The three values are recomputed
by questioning the engine, then compared with what you wrote. Several paths give
the same answer, and all of them count.
