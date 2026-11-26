# Deliver an image without the daemon ever touching it

A delivery machine must prepare three image archives for a site that has no
access to the registry. You work in
`/opt/dsoxlab-images-exporter-sans-demon`, where `skopeo` is already installed
as a pinned image: the `skopeo` command in that directory calls it, and you
have nothing to install.

The image to deliver is **`busybox:1.37.0-musl`**, pinned by its index digest:
`sha256:f6a95d611e0a8780fabdb2aec43e31275b2720dfefa3e41b16835bfc42454478`.

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

## Brief

Work on `docker.lab`, in `/opt/dsoxlab-images-exporter-sans-demon`. The
`skopeo` launcher is supplied there: call it with `./skopeo`, you have nothing
to install. `A-LIVRER.txt` recalls the image and its digest.

1. **`livraison/socle-oci.tar`** is an **OCI** format archive: it carries an
   `oci-layout`, an `index.json` and `blobs/sha256/` entries. It really holds
   the image to deliver, checked by its configuration digest.
2. **The daemon never pulled that image.** `docker image inspect
   busybox:1.37.0-musl` must fail. Copy from the registry with `docker://` as
   the source transport; a `docker pull` followed by `docker save` is refused,
   since it requires from the daemon what a host without a daemon cannot do.
3. **The archive loads as a named image**, `livraison.test/socle:1.0`, and
   **its layers are the source's**. The local identifier does change: that is
   expected, the section on transport says why.
4. **`livraison/socle-arm64.tar`** holds the **arm64** architecture, while this
   host is amd64, and its manifest differs from the main archive's.
5. **`livraison/socle-docker.tar`** is in **docker-archive** format: it carries
   a flat `manifest.json` and **no** `oci-layout`.

Not graded: the archive permissions. `skopeo` writes 0644 on its own, so
requiring it would measure nothing; `docker save` is the one writing 0600, and
that contrast belongs to the lesson.

Do not change the daemon configuration and do not touch the other images on the
machine.
