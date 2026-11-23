# Three refused accesses, and not one single cause

## The situation

Three containers of the same chain are not doing their job. The ticket says
"permission problem on the volumes", and that is exactly the kind of wording
that costs a morning: it files three distinct failures under one word.

The first container cannot write into its directory. Neither can the second.
The third did not even start. Apply the reflex gesture, a wide `chmod` on the
three directories, and **only one of the three failures goes away**. The other
two are untouched, because they had nothing to do with rights.

## The goal

Read the messages, and read them **word by word**:

```text
perm-a            cannot write into /ref
perm-b            cannot write into /donnees
perm-c            did not start
temoin-sans-bit   did not start either, for the same reason, and you WILL NOT
                  REPAIR IT
```

Try both writes yourself. The engine does not return the same sentence in the
two cases, and that is the whole key: one speaks of the **file system**, the
other of **rights**. The first accuses the mount, the second says the mount
agrees and the rights are what refuse.

Fill in the three lines of `/opt/lab-permission/reponses.txt`:

```text
rw_b=<what the inspection of perm-b declares for its mount>
uid_b=<the uid perm-b runs as>
code_c=<the exit code of temoin-sans-bit>
```

The first answer is the one carrying the lab: it proves that `perm-b`'s failure
is **not** `perm-a`'s, although the symptoms look alike.

The brief is also laid down in `/opt/MISSION.md`.

## The third failure is not a matter of rights

`perm-c` does not start, and its exit code is the one of the file **found but
not executable**, already met in the lab on code 127. Here the cause is
elsewhere: the script comes from a mount, and **a mount changes no mode**. The
file's mode is the host's, and it will stay so.

That is why a `chmod` played **inside** the container is of no use, and why the
container does not stay up long enough to play anything in it anyway.

## The repair, and this is where the lab has an opinion

The three containers must work: write for the first two, run and have produced
its trace for the third.

But `perm-b` must get there **without going root**. Going root would fix the
symptom in one option, and the check expressly refuses it: the lab on
permissions has shown the right answer, which is to align the group. A
troubleshooting lab must not undo what a method lab taught.

## What is graded

The **system state**. The three expected values are read at grading time, and
none of them is written in the checks.

Each repair is proven by its **effect**: a real write for the first two, the
script's trace for the third. Not a command-line option, which would only say
what you typed.

## What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running. **Three
containers hit a refused access**, and the three causes have nothing in common:

```text
perm-a            does not write into /ref
perm-b            does not write into /donnees
perm-c            did not start
temoin-sans-bit   did not start either, for the same reason
```

**Start by trying both writes yourself**, and compare the two messages. They do
not say the same thing, and that is the whole key to the diagnosis.

The first three answers go into `/opt/lab-permission/reponses.txt`, one line per
entry, with no space around the equals sign.

### 1. What the inspection declares for `perm-b`'s mount

On the `rw_b=` line.

This is the answer carrying the lab. The first two containers hit a refused
write, and the two messages already differ: one speaks of a **read-only file
system**, the other of a **permission denied**.

The first accuses the **mount**. The second says the mount allows writing, and
that the **rights** are what refuse. Inspecting the container separates the two
cases in one word, and that word is what is asked.

### 2. The uid `perm-b` runs as

On the `uid_b=` line.

A container does not necessarily run as root, and when it runs under an
application uid, the rights of the mounted directory concern it like any other
user of the system. The container can answer for itself.

### 3. The exit code of `temoin-sans-bit`

On the `code_c=` line.

This is the code of the file **found but not executable**. The cause is in the
script's mode, which comes from the host: **a mount never changes one**.

**Do not repair `temoin-sans-bit`**: it stays broken so that its code is
readable to the end. A repaired container no longer carries the code being
asked for, and a check verifies that it stayed as it was.

### 4. Repair all three, without going root

```text
perm-a   must be able to write into /ref
perm-b   must be able to write into /donnees, WITHOUT being root
perm-c   must RUN, and have produced its trace
```

Three different gestures, and that is the whole lab:

- a **mount** cannot be changed on an existing container;
- a directory's **rights** are aligned on the container's group, as the lab on
  permissions has shown. Going root would fix the symptom, and the check
  expressly refuses it;
- a **file mode** is corrected on the host, since the mount does not change it,
  and the container is relaunched afterwards. In that order: the reverse would
  relaunch a container failing for the very same reason.

Each repair is proven by its **effect**: a real write for the first two, the
script's trace for the third.

### What is not graded

The command you typed. The values can be found in several ways, and the three
repairs can be done by any means producing the expected effect, root excepted
for the second.
