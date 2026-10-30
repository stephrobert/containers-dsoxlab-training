# The database was answering from the internet

## The situation

An audit goes through your server and reports one line that chills you: an
internal application's database answers from the outside. Nobody opened it.
There is no firewall rule allowing it, and you are certain you never exposed
anything.

You read the command that started the container again. It says:

```text
docker run -d --name base -p 5432:5432 postgres
```

The `-p 5432:5432` does not publish "on the machine". It publishes on **all
interfaces**, because the publication address is **optional** and its default is
the most open of the three possible ones. The port was open from day one, and it
never appeared in any decision.

## The goal

Correct three badly published containers, one per posture. All three are built
on the image `lab-publication:1.0`, which listens on its port 80 and answers a
token.

```text
vitrine   published on ALL interfaces
          → must only be published on 127.0.0.1, port 18080 of the host

annexe    publishes NOTHING
          → must be published only on the ROUTABLE address, port 18081

interne   published on port 18082 of the host
          → must publish NO port at all, while staying reachable by the other
            containers
```

Keep the names: the checks look for them by name. The brief is also written to
`/opt/MISSION.md`, with the machine's routable address.

## What you need to know before starting

**A container's publication cannot be changed on a running container.** No
command changes the `-p` of an existing container: it has to be destroyed and
recreated.

That is why the image carries its listener: relaunching a container needs no
particular command.

```bash
docker run -d --name <name> <publication options> lab-publication:1.0
```

The token changes at every recreation, and that is normal: the checks read the
service's answer, not yesterday's token.

## What is graded

The **state of the system**, and it is measured twice for each posture: what the
engine **declares** it publishes, and what the machine actually **does**.

The two can diverge, and that is why both are measured. One detail that matters
here: the checks read the service's **answer**, never the connection alone.
Docker's proxy accepts a connection before anything is listening, so a port that
"answers" may well lead nowhere.

## The posture that gets forgotten

Publishing nothing. A service only other containers need has no reason to be
published: they reach it through the network, with no port on the host.

Publishing is the reflex, and that reflex is what exposes databases.
