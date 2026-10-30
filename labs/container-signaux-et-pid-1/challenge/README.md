# What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running. The `fragile`
container is running, and the sources of its image are readable in
`/opt/lab-signaux`: `app.sh`, `entree.sh` and the `Dockerfile`.

The application **does** know how to receive a SIGTERM: its code traps it,
writes `sigterm-recu` and exits with zero. It never does.

## 1. Stop `fragile`, and keep the symptom

Its exit code must **not** be zero, and its logs must **not** carry
`sigterm-recu`.

That is deliberate: this container is the evidence. **Do not fix it**, do not
remove it, do not re-run it from a corrected image. The next three checks
compare against it.

Also look at how long the shutdown takes. That is not a detail, it is the
signature of the failure.

## 2. An `img-corrige:1.0` image whose PID 1 is the application

The check runs a throwaway container from your image and reads the name of the
number one process. It must be the application's, not the entry script's.

**The entry script must stay and keep its preparation.** Emptying it would fix
the signal by removing the script's reason to exist, and a check in point 4
verifies that its line still appears in the logs.

One word separates the two images.

## 3. A `robuste` container, stopped, code zero

Run a container named `robuste` from your corrected image, then stop it. Its
exit code must be `0`.

A non-zero code on a requested shutdown is exactly what was skewing the alerts:
it looks like an incident, and an automatic restart can fire on it for nothing.

## 4. Its logs carry the proof of the signal

`sigterm-recu`, written by the application itself when it receives it.

Why this check on top of the exit code: a zero could come from an application
that terminated for another reason. This line leaves no room for that doubt.

The logs must **also** carry `preparation-faite`, for the reason given in point
2.

## What is not graded

The way you fix it. Making the application PID 1 from the entry script,
invoking it directly from the `ENTRYPOINT`, or going through an init that
forwards signals all reach the same state. All three count.
