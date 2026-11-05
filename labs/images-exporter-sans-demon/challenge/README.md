# Brief

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
   expected, and the scenario says why.
4. **`livraison/socle-arm64.tar`** holds the **arm64** architecture, while this
   host is amd64, and its manifest differs from the main archive's.
5. **`livraison/socle-docker.tar`** is in **docker-archive** format: it carries
   a flat `manifest.json` and **no** `oci-layout`.

Not graded: the archive permissions. `skopeo` writes 0644 on its own, so
requiring it would measure nothing; `docker save` is the one writing 0600, and
that contrast belongs to the lesson.

Do not change the daemon configuration and do not touch the other images on the
machine.
