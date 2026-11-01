# A registry reference is not an offline delivery

On `docker.lab`, `127.0.0.1:15006/catalogue/appli:1.0` is available only from
`dsoxlab-air-gap-registry`. Another environment will have no access to this
registry. Sending its reference, a manifest alone or an exported container
filesystem will not let the recipient load and run the original image.

Prepare a complete delivery under `/opt/lab-air-gap`:

- `livraison.tar`: a Docker archive containing the published image, including
  its configuration and every layer, tagged `dsoxlab-air-gap:livree`;
- `livraison.tar.sha256`: its SHA-256 receipt, naming `livraison.tar`
  without an absolute path so the receipt remains portable.

## Mission

Use Skopeo, or another tool that produces an equivalent Docker archive, to
retrieve and package the published product. The delivery must remain usable
after the registry stops, without Docker's local image cache filling gaps.
The recovered image must keep its identity and print the prepared release
with `--network none` and `--pull never`.

The checks copy every archived blob using an independent Skopeo directory
transport, stop the source registry, reconstruct the image from that directory,
load it and execute it without a network. They restore the registry afterward.
No second VM or public network access is required.

For this packaging bench only, the source is intentionally HTTP on loopback;
Skopeo requires `--src-tls-verify=false` for that source. This is not a nominal
configuration for a network registry. Do not modify its storage, source product
or bench files, and do not prune Docker globally.

You can verify the portable receipt from the delivery directory:

```bash
cd /opt/lab-air-gap
sha256sum --check livraison.tar.sha256
```
