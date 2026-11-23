# The disk is full, and no volume is to blame

## The situation

The server raises an alert: the partition holding `/var` is at 96%. You look
for the culprit among the volumes, since that is where data lives. They weigh a
few hundred megabytes in total.

You look among the images. There are many, but the numbers do not add up either.

What is filling the disk is the containers themselves. Not their volumes:
**them**. Each has a write layer of its own, which receives everything it writes
outside a volume, and that layer is an ordinary directory on your disk. A
service that logs to a file instead of its standard output fills it quietly,
for months.

## The goal

Go and see that place, and observe that there is nothing mysterious about it.
The container `entrepot` is running, and it has written nothing yet.

Fill in the two lines of `/opt/lab-stockage/reponses.txt`:

```text
pilote=<the storage driver the engine uses>
ecriture=<the ABSOLUTE path of `entrepot`'s WRITE layer, on the host>
```

Then, **from the container**, do two things:

1. write the line `ceci-a-ete-ecrit-dans-le-conteneur` into
   `/trace-ecriture.txt`;
2. create a `/charge.bin` file of 5 Mo.

Both must be found on the **host's disk**, in the write layer.

The brief is also written to `/opt/MISSION.md`.

## What you will observe

That the file written in the container reads from the host **immediately**, with
no export and no particular command. A container does not write somewhere else.

And that the layer contains **only the differences**: after one write, it
carries only that file, not a copy of the filesystem. That is what makes
containers light, and it is also what makes them grow without being seen
growing.

## What is graded

The **state of the system**, and the fourth measurement is a **weighing**: the
layer must weigh at least what you wrote into it. That is the consequence that
matters in operations, and the one discovered too late.

A file created in a volume or in memory would not appear there, and that is
precisely the difference the volume labs taught.

## A word on tooling

`/var/lib/docker` is not readable by an ordinary account. You have to be root to
look, that is normal, and it is not the lab's subject.

Mind the choice of load file too: a file **allocated** without being written can
occupy no block on the disk, and the weighing would count it as zero. Write real
bytes.

## What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running on the
`overlay2` driver. The container `entrepot` is **already running**, and it has
written nothing yet.

The first two answers go into `/opt/lab-stockage/reponses.txt`, one line per
entry, with no spaces around the equals sign.

### 1. The engine's storage driver

On the `pilote=` line.

There is not one single way to stack layers: the engine knows several, and the
choice changes the paths, the performance, and even which filesystems are
acceptable under its root. Knowing which one is in place is the first question
of any storage diagnosis.

The engine states it in its general information, next to the directory where it
keeps everything.

### 2. `entrepot`'s write layer

On the `ecriture=` line, an absolute path on the host.

The container's inspection gives **four** paths, and they do not have the same
role: one holds the image's read-only layers, one is the merged view the
container sees, one is a working directory, and one receives the writes.

Only the last one is asked for.

### 3. A trace, written inside and read outside

From the container, write the following line into `/trace-ecriture.txt`:

```text
ceci-a-ete-ecrit-dans-le-conteneur
```

The check reads it **twice**: inside the container, then on the host's disk, in
the layer you announced. No export, no copy, no particular command.

That is the lab's point: a container does not write somewhere else.

### 4. A 5 Mo load, and a weighing

From the container, create a `/charge.bin` file of **5 Mo**.

The check **weighs the layer** on the host: it must be at least 5 Mo. What a
container writes is not free, it occupies the machine's disk, and it is the
cause of failures that get badly diagnosed.

**Mind the choice of tool**: a file *allocated* without being written can occupy
no block on the disk, and the weighing would count it as zero. Write real bytes.

### A word on tooling

The engine's root is not readable by an ordinary account. You have to be root to
look, that is normal, and it is not the lab's subject.

### What is not graded

The command you typed. Both values can be read in several ways, and both writes
are made from the container by any means. Only the state counts.
