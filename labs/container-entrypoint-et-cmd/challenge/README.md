# What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running. Two images are
already built, and **their Dockerfiles are readable** in `/opt/lab-entrypoint`:
read them, that is half the exercise.

```text
img-cmd:1.0          declares only a CMD
img-entrypoint:1.0   declares an ENTRYPOINT and a CMD
```

Four containers to produce, and **no `--rm`**: it is in the logs that what ran
is read.

## 1. `defaut`: the reference point

From `img-cmd:1.0`, **with no argument**. Its logs must carry
`defaut-de-limage`.

A `CMD` is what the image executes when nothing is asked of it. Nothing else is
graded here: it is the reference the next three compare against.

## 2. `remplace`: a CMD does not resist

From `img-cmd:1.0`, its logs must carry `remplacement-total`, and **not**
`defaut-de-limage`.

What you pass after the image name takes the place of the `CMD`, **entirely**.
A command is expected there, not a plain word: if you pass only a text, the
container will try to execute it.

The absence of the default is graded as much as the presence of your text: it is
what proves the replacement.

## 3. `complete`: an ENTRYPOINT does resist

From `img-entrypoint:1.0`, its logs must carry the entrypoint prefix **and**
`complement-cmd`.

The same action as point 2 no longer has the same effect: the argument replaces
nothing, it becomes the entrypoint's argument, taking the CMD's place. That is
the surprising point, and the whole subject of the lab.

## 4. `contourne`: the rule has a way out

From `img-entrypoint:1.0`, its logs must carry `sans-prefixe` and **not** the
prefix.

An `ENTRYPOINT` can be replaced, but only through the **option meant for it**.
Passing an argument is not enough: you would fall back on case 3. That is what
separates it from a `CMD`: overriding is a deliberate action, not a side
effect.

## What is not graded

The command you typed, nor the form you use. Two of the four results are
reached as well in exec form as in shell form, and both count.
