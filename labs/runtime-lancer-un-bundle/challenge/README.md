# A watcher that touches nothing

## The situation

On `oci.lab`, a Debian 13 with no container engine, the team wants a
`veilleur` container that runs all the time, started directly by runc. A first
attempt was made: it stopped, and it still holds the identifier.

The busybox 1.37.0 image is ready in the `/srv/oci-busybox` layout, under the
`1.37.0` tag. runc, umoci, skopeo and jq are installed. You are `root` through
`sudo`.

## What you must obtain

1. The bundle **`/srv/veilleur`** comes from the image of `/srv/oci-busybox`.
   Its `config.json` runs **`sleep infinity`**, sets the host name
   **`veilleur`**, and makes the root **read-only**.
2. The container **`veilleur`** runs from that bundle, detached: it keeps
   running after you log out.
3. Seen from inside, it carries the name `veilleur`, and a write at its root
   is refused.
4. No stopped container is left in `runc list`.

## Useful landmarks

The lesson builds a bundle in two ways: by hand with `runc spec`, or from an
image with `umoci unpack`. Here, start from the image. Careful: the
`config.json` umoci writes does not make the root read-only, the one from
`runc spec` does.

A detached container needs `process.terminal` set to `false`. A stopped
container keeps its identifier until it is deleted.

## How you will know it works

The tests read `/srv/veilleur/config.json`, the state runc gives for
`veilleur`, the list of its containers, and run `hostname` and a write in the
container with `runc exec`.

```bash
dsoxlab check runtime-lancer-un-bundle
```
