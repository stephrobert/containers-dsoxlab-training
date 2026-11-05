# Export an image without the daemon

This lab delivers a pinned registry image as three archives, on a host whose
daemon must never pull it. A supplied launcher provides Skopeo 1.22.3, the
publisher's version and not the distribution's.

Five checks prove the delivery, and each fails before any work. The OCI archive
carries the expected image, checked by its layers; the daemon's local store
holds no trace of the source image, which a `docker pull` followed by
`docker save` could not achieve; the archive loads as a named image, since
Skopeo accepts a nameless destination and only `docker load` shows the
consequence; the arm64 archive really holds arm64 on an amd64 host; and the
docker-archive is the historical format, with its `repositories` entry and its
`<id>/layer.tar`.

What is not graded, and why: the archive permissions. Skopeo writes 0644 by
itself, so requiring it would reward the initial state.

Two measured facts shape the lab. On a containerd store the local identifier is
the manifest digest, so it legitimately changes across a format conversion: the
lab shows what it becomes instead of requiring it to survive. And the layers of
an image inside the daemon are the uncompressed diff_ids, never comparable to
the registry's compressed digests, whichever tool reads them.

Cleanup removes only what the setup placed, from markers it writes itself.
