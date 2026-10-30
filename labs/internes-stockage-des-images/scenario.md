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
