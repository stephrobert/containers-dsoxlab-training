# Deliver an image without the daemon ever touching it

A delivery machine must prepare three image archives for a site that has no
access to the registry. You work in
`/opt/dsoxlab-images-exporter-sans-demon`, where `skopeo` is already installed
as a pinned image: the `skopeo` command in that directory calls it, and you
have nothing to install.

The image to deliver is **`busybox:1.37.0-musl`**, pinned by its index digest:
`sha256:f6a95d611e0a8780fabdb2aec43e31275b2720dfefa3e41b16835bfc42454478`.

## What must be produced

1. **`livraison/socle-oci.tar`**, an **OCI** format archive, copied **straight
   from the registry**, carrying the full destination name
   `livraison.test/socle:1.0`.
2. **`livraison/socle-docker.tar`**, the same image in **docker-archive**
   format, with the same destination name. The two formats share neither
   structure nor size, and the delivery must show it.
3. **`livraison/socle-arm64.tar`**, an OCI archive of the **arm64** variant of
   that same image, while this host is amd64.

## What the daemon must never do

**The daemon must not have pulled the image.** That is the whole point: `skopeo`
talks to the registry itself, without going through it. After your work,
`docker images` must carry no trace of `busybox:1.37.0-musl`.

A `docker pull` followed by `docker save` would produce an archive, and would be
refused: that path requires the daemon to pull the image, which a host without a
daemon cannot do.

## What survives the transport, and what changes

Load `livraison/socle-oci.tar` into the daemon to see for yourself. Three
numbers are called "identity", and the transport does not treat them alike:

- the **local identifier** (`.Id`) **changes**, and that is expected: this
  engine stores images with containerd, where that identifier is the manifest
  digest, and the format conversion rebuilds the manifest;
- the **configuration digest**, which `skopeo inspect` returns as `Digest`,
  **survives**;
- the **layers** (`RootFS.Layers`) **survive**.

A transport that changed the layers would not have delivered the same image.

## Two traps you will hit

**A tag and a digest together are refused.** `name:tag@sha256:...` is not how it
is named: skopeo answers `references with both a tag and digest are currently
not supported`. Name it by digest alone, or by tag alone.

**A destination with no name gives an image with no name.** `docker load` then
prints `Loaded image ID: sha256:...` instead of `Loaded image: ...`, and the
site receives an image it must rename before it can use it.

**And a docker-archive cannot be rewritten.** If you start a delivery over,
skopeo refuses: `docker-archive doesn't support modifying existing images`.
Remove the file first. An `oci-archive` accepts it: one more difference between
the two formats.

Do not change the daemon configuration and do not touch the other images on the
machine.
