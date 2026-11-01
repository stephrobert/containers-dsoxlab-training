# Credentials are not permissions

The release team has a TLS registry and two valid accounts, but neither can
distribute an image. Giving both accounts administrator access would turn
the deployment machine into a publisher.

Restore the release path without widening its boundary. The publisher lives
on `docker.lab`; the reader uses the separate engine on `docker-client.lab`.
A newly published product must arrive unchanged at its immutable digest,
and the reader must remain unable to upload.

Work in `/opt/lab-registry-rights` on the VMs, not in a local working directory.
See [the requirements](challenge/README.md).
