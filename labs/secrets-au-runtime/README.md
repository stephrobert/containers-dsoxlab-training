# Runtime secrets are files, not image content

Environment variables can appear in `docker inspect`, process environments,
debugging and crash output. Image build arguments and copied files can survive
in image history or layers. Runtime file delivery avoids these common channels.

For a neutral project `demo-mailer`, Compose's top-level `secrets` can declare
a private source file; a service grants that secret with a `target` filename
under `/run/secrets`. Local Compose typically implements file secrets as
read-only bind mounts. It is not Swarm's encrypted secret store: the host source
must still be protected, and a Docker administrator can read it.

The supplied source is root-owned mode 0600; the container's root can read it
without DAC_OVERRIDE. Never log the value. A digest can show that the
application consumed the right bytes without publishing them. The checker keeps
raw inspect and log data on the VM and returns only a leakage verdict. It also
requires the supplied immutable base image, rather than inspecting image layers
that might contain a copied secret.

The engine, Compose and Python 3 must already be available.
See [the challenge](challenge/README.md).
