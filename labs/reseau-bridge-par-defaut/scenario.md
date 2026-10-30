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
