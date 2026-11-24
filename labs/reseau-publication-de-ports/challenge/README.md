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

## What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running. Three containers
are **already running**, all built on the image `lab-publication:1.0`, which
listens on its port 80 and answers a token.

All three are badly published, each in its own way. The machine's routable
address is given in `/opt/MISSION.md`, and you can also read it with
`ip -4 addr`.

The brief is also written to `/opt/MISSION.md`.

### 1. `vitrine`: on the loopback only

It is published on **all** interfaces. It must only be published on
`127.0.0.1`, port **18080** of the host.

`-p 18080:80` does not publish "on the machine": the publication address is
**optional**, and its default is the most open of the three. Name it.

The check verifies two things: what the engine declares, and that the service
still answers on the loopback. Publishing is not serving.

### 2. `vitrine` is no longer reachable from the network

That is the observable consequence, and the only one that really counts.

The previous check reads what the engine **declares**; this one tests what the
machine actually **does**. The two can diverge.

### 3. `annexe`: on the routable address alone

It publishes **nothing**. It must be published on the machine's routable
address, port **18081**, and only there.

That is the real case that gets forgotten: a service you want to reach from the
network, but not from everything running on the machine.

The check verifies it **both** ways: reachable through the routable address, and
**not** through `127.0.0.1`. A publication on all interfaces would satisfy the
first way alone.

### 4. `interne`: no published port, and still reachable

It is published on port 18082 of the host. It must publish **no** port at all,
while staying reachable by the other containers.

That is the posture that gets forgotten. A service only other containers need
has no reason to be published: they reach it through the network, with no port
on the host.

The two requirements are inseparable, and that is why they make one check:
publishing nothing would be trivial by destroying the container.

### What you need to know before starting

**Publication cannot be changed on a running container.** No command changes the
`-p` of an existing container: it has to be destroyed and recreated, under the
**same name**.

The image carries its listener, so relaunching a container needs no particular
command:

```bash
docker run -d --name <name> <publication options> lab-publication:1.0
```

The token changes at every recreation, and that is normal.

### A word on tooling

Do not settle for a connection that succeeds. Docker's proxy accepts before
anything is listening: **read the answer**. `nc -w 3 <address> <port>` must print
a `jeton=...` line.

## What is graded

The **state of the system**, and it is measured twice for each posture: what the
engine **declares** it publishes, and what the machine actually **does**.

The two can diverge, and that is why both are measured. One detail that matters
here: the checks read the service's **answer**, never the connection alone.
Docker's proxy accepts a connection before anything is listening, so a port that
"answers" may well lead nowhere.

### What is not graded

The command you typed. The containers can be recreated on the command line as
well as through the API. Only the state counts.
