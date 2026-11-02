# What is asked

On `docker.lab`, a disposable Debian 13. In `/opt/lab-variantes`, a base
`compose.yaml` **you do not modify**, and two things that do not state the same
version:

- the **image** carries its own `version.txt`, frozen at build time;
- the **disk** carries `src/version.txt`, with another value.

The service returns the version it reads at `/app/src/version.txt`. That is the
whole measuring device: its answer says unambiguously whether it reads the image
or the host's disk.

It listens on `127.0.0.1:18081`.

## 1. A development variant, which mounts the sources

Write `/opt/lab-variantes/compose.dev.yaml`, to be **derived** from the base
file and not copied from it. It mounts `/opt/lab-variantes/src` onto `/app/src`
in the container, so that a change on disk shows without rebuilding.

## 2. A deployment variant, which mounts none

Write `/opt/lab-variantes/compose.deploiement.yaml`, derived from the same base
file. It mounts **nothing**: the service reads the image's version there.

A development mount left behind in deployment is the classic incident. It does
not show in the base file, it shows in the **effective configuration**, and that
is where the check looks.

## 3. The deployment, up

Leave the **deployment** variant in service, in the Compose project
`dsoxlab-variantes`. That is the expected final state, and the service must
answer the **image**'s version there.

## 4. The optional service, under its profile

The base file declares a `debug` service under the `debug` profile. Check that
it stays **absent** from both variants' effective configuration as long as that
profile is not requested, and **present** as soon as it is.

You have nothing to write for this: you have to not break it while deriving.

## The expected final state

The deployment variant is running, with no mount at all, and serves the image's
version. Both variant files exist, derive from the base file, and the base file
is unchanged.

## What is not graded

How you derive: `include`, `extends`, several `-f`, or a `COMPOSE_FILE`. The
check reads the effective configuration, which is the only thing that counts,
and never the command you typed.
