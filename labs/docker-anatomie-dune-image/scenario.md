# The Dockerfile says one thing, the image says another

## The situation

Your team hosts about thirty images built on the same Debian base. The build
server's disk is filling up, and management wants a figure: "how much do these
images really weigh?"

You add up what `docker images` shows in the SIZE column, and you get a total
far above the space actually used. Someone tells you that "layers are shared",
which is true and gets you nowhere until you know **which ones** and **how
many**.

So you open a Dockerfile to count its layers, and a second surprise is waiting:
the count does not add up. Not every instruction creates a layer, and one of
them creates a layer without looking like it.

## The goal

Dissect an image instead of reading its Dockerfile. Two images are already
built on the machine, from the **same** base and with the **same** first
instructions:

```text
greffe:1.0    the one being dissected
greffe:2.0    the one starting from the same base layers
```

Their Dockerfiles can be read in `/opt/lab-anatomie`. **Do not trust them**:
the engine is the only source.

Fill in the four lines of `/opt/lab-anatomie/reponses.txt`:

```text
couches=<the number of layers of greffe:1.0>
partagees=<the number of layers the TWO images have in common>
propres=<the number of layers of greffe:2.0 absent from greffe:1.0>
revision=<the revision greffe:1.0 carries in its configuration>
```

The brief is also written to `/opt/MISSION.md`.

## What is graded

The **state of the engine**, never the commands you typed. All four values are
recomputed at grading time by questioning the images, then compared with what
you wrote.

The revision is the clearest case: it is written in **no file** on this
machine, it is not in the image history either, and it is drawn at random on
every pass. It lives in the image's **configuration**, next to its environment
and its default command, and that is the whole point of the question: an image
is not only a content.
