# 79 MB for a three-hundred-byte script

## The situation

An application image weighs 79 MB. You look at what it contains: a
three-hundred-byte shell script, and four numbers in a file.

The rest is the base. A full distribution, with its package manager, its C
library, its manual pages, to do an addition.

Changing the `FROM` line takes a second. And the image no longer starts, on a
message that blames the script.

## The goal

The image `appli:lourde` works: run it, it prints its token, a sum and a
maximum. Then weigh it.

An Alpine base is already on the machine, under the name `lab-socle-leger:1.0`,
and it weighs 8 MB. Build `appli:legere` on it.

```text
print the same token, the same sum and the same maximum as appli:lourde
weigh a fraction of appli:lourde
be built on the light base
COMPUTE, not recite
```

The context is in `/opt/lab-migration/appli`. Do not modify `appli:lourde`: it
is the reference you are compared against.

The brief is also laid down in `/opt/MISSION.md`.

## Changing the `FROM` line will not be enough

Try it, and read the message.

```text
exec /usr/local/bin/traiter: no such file or directory
```

Through `sh` it is sharper still, and it carries the code 127 already met:

```text
sh: /usr/local/bin/traiter: not found
```

Go and check: the script is there, executable. **So it is not the script that is
missing.** What is missing is the interpreter its shebang calls for, and the
kernel returns the error under the name of the file it was handed.

It is the same mechanism as `troubleshoot-exit-127`, and the same family of
misleading message as `images-contexte-de-build`: **the engine reports what it
sees, not what is there.**

## Migrating means adapting

The script uses two constructs its old base gave it and the new one does not
have. No change of `FROM` will put them there.

You have two routes, and both pass the checks: rewrite what depended on the old
base, or install on the new one what is missing. The first is the one this lab
argues for: adding a 2 MB interpreter for two constructs, one of which fits in a
loop, amounts to paying for the base you have just left.

## What is measured

| Base | Size |
| --- | --- |
| `debian:13-slim` | 78.9 MB |
| `alpine:3.22` | 8.3 MB, 9.5 times less |

Measured on this machine, on 2026-10-30. And the POSIX equivalent of the script
gives the same result on both bases: `somme=26 max=11` on either side.

## What is graded

The **system state**, at four places that do not overlap: the result on the
repository's data, the base actually used (read in the layers), the weight
relative to the reference, and the computation on data the image **has never
seen**.

That last check is there because the other three would pass on an application
printing a frozen result. The repository's data does not change during a
session; the check's data does.

No threshold and no result is written in the repository: the data is drawn on
every pass, the result is recomputed at grading time, and the weight ceiling is
derived from the reference image.
