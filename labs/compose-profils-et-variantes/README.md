# compose-profils-et-variantes

**Audience:** the learner.

An input file declares, an effective configuration decides. This lab makes you
measure the gap, on the case that costs the most: a development mount left
behind in deployment.

## What you will be able to do

- Derive two variants from one base file, without ever modifying it.
- Read the **effective configuration** rather than the input file, and say why
  that is the only reading that counts.
- Recognise a development mount still active in deployment, including the
  particularly treacherous case where it mounts nothing at all.
- Keep an optional service out of the resolution with a profile, and bring it in
  on demand.

## How it is graded

Four checks of equal weight:

1. the deployment variant **runs**, with no mount at all, and serves the image's
   version;
2. the development variant does mount the sources, checked in the effective
   configuration **and** at run time;
3. the base file carries no mount, and the deployment variant declares none;
4. the optional service is absent without its profile, and present with it.

The measuring device is the gap between two versions: the image carries its own,
the disk carries another. The service's answer says which of the two it reads.

## What the lab does not do

It imposes no derivation mechanism on you. `include`, `extends`, several `-f`, a
`COMPOSE_FILE`: all of them are fine, because the check reads the result and not
the method.
