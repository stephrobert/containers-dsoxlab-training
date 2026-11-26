# An image to check before accepting it

## The situation

On `oci.lab`, a Debian 13 with no container engine, the team only wants to
accept images it has checked itself. It gives you two tasks: copy busybox
1.37.0 by digest and write down what it contains, then examine a layout
received from elsewhere, `/srv/suspect`, in which one file was modified.

skopeo, jq and umoci are installed. You are `root` through `sudo`.

The reference image is the busybox 1.37.0 index:

```text
docker.io/library/busybox@sha256:a7dbc319b1438115a207e11930dc4bb3e643dcb3ec0bdd694bb36cd8fad289ec
```

## What you must obtain

1. **`/srv/etal`** is an OCI layout holding busybox 1.37.0 for
   `linux/amd64`, copied by that digest, under the tag **`1.37.0`**.
2. Every blob of `/srv/etal` carries the hash of its name.
3. The file **`/srv/reponses/manifeste-amd64`** contains the digest of the
   `linux/amd64` manifest of that image.
4. The file **`/srv/reponses/blob-altere`** contains the **name** of the blob
   of `/srv/suspect` that was modified.

An answer is written on one line, with or without the `sha256:` prefix.

## Useful landmarks

`/srv/suspect` holds two images, `amd64` and `arm64`, so six blobs. The
modification did not change the size of the file: only the hash gives it
away. The modified blob is drawn at random on every `dsoxlab reset`.

The digest of a platform is read in the index served by the registry, not in
the `Digest` field of a `skopeo inspect` given `--override-arch`.

## How you will know it works

The tests read `oci-layout` and `index.json` of `/srv/etal`, recompute the
hash of each of its blobs, and compare your two answers with the expected
digest and with the blob the setup modified.

```bash
dsoxlab check image-lire-a-la-main
```
