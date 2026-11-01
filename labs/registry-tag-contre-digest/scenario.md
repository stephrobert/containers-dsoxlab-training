# Stable did not retain the same image

On `docker.lab`, the registry at `127.0.0.1:15002` received two releases as
`catalogue/appli:stable`. The tag now points to the second. The container
`dsoxlab-digest-app`, launched by that tag, runs the wrong product.

The first delivery receipt is `/opt/lab-registry-digest/livraison.json`.
It gives its registry reference with the manifest digest and expected product.
The `appli/` context now contains the second release: rebuilding it does not
recover the first.

## Mission

- Retrieve the first delivery's image from the registry.
- Replace `dsoxlab-digest-app` with a running container from that image.
- Launch it by its registry reference with digest, not a recreated tag or its
  configuration ID.
- `docker exec dsoxlab-digest-app cat /release.txt` must return the receipt's
  original product.

Keep the `stable` tag and registry intact. The goal is to recover immutable
content despite a moved tag, not rewrite the registry's history.
The HTTP registry listens only on loopback.

The manifest digest and configuration ID are distinct identities. Checks verify
the image actually running, its startup reference, product and availability of
the original manifest through an independent client.
