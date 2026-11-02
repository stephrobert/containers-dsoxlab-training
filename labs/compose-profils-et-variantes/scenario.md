# Scenario

The team has a single Compose file, and two ways of using it. In development the
sources are mounted into the container: you edit, you reload, you do not
rebuild. In deployment nothing is mounted, and the image carries everything.

For six months both uses have lived in the same file, with commented-out lines
that get uncommented "just for one test".

Last month a rollout went out with the mount still active. The service was
reading a host directory that did not exist on the production machine: it
started, it answered, and it served a version three weeks old. Nobody saw it for
two days, because the file itself looked right.

You are asked to separate the two uses for good, and to leave nothing to
uncommenting.

## Mission

Derive from the base file a development variant that mounts the sources, and a
deployment variant that mounts none. Leave the second one in service.

The base file is not to be modified. What is expected in detail is in
`/opt/lab-variantes/MISSION.md`.
