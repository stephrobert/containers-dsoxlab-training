# What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running. Two images and
two bases are already there:

```text
appli:lourde          it WORKS, and weighs 79 MB
lab-socle-lourd:1.0   the Debian base, 79 MB
lab-socle-leger:1.0   the Alpine base, 8 MB
```

The context is in `/opt/lab-migration/appli`.

**Start by running `appli:lourde` and weighing it.** Then change the `FROM` line
and build: read the message.

## 1. The light image must give the right result

`appli:legere` must print the same token, the same sum and the same maximum as
the reference.

The data is in `donnees/valeurs.txt`, and its values are drawn on every pass.
The check recomputes the result itself: it does not compare against a number
written somewhere.

If the message names the script and says it cannot be found, **go and check**:
it is there, executable. What is missing is the interpreter of its shebang.

## 2. It must be built on the light base

The check compares the **layers**: the light base's must be the prefix of the
image's.

An image can perfectly well work and weigh the right amount without having
changed base. The mission is to migrate, and that is read in the layers, not in
a version file.

## 3. It must weigh a fraction of the reference

The threshold is **derived** from `appli:lourde`, weighed at grading time: a
third of it. The light base weighs 8 MB against 79, so the margin is very wide.

An image that stays this heavy has not changed base, or carries along what the
base already provides.

## 4. It must compute, not recite

The check gives it data it **has never seen**, through a mount on `/donnees`,
and expects the right result.

The first three checks would pass on an application printing a frozen result:
the repository's data does not change during a session. That is why this one
exists.

## Migrating means adapting

The script uses two constructs its old base gave it. You have two routes, and
both pass the checks:

- **rewrite** what depended on the old base;
- **install** on the new one what is missing.

The first is the one this lab argues for: adding a 2 MB interpreter for two
constructs, one of which fits in a loop, amounts to paying for the base you have
just left. The choice remains yours.

## What is not graded

The command you typed, and the path you chose. Do not modify `appli:lourde`: it
is the reference you are compared against.
