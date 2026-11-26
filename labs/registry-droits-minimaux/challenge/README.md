# Credentials are not permissions

## The situation

The release team has a TLS registry and two valid accounts, and neither can
distribute an image. Giving every right to both would restore delivery, and
would turn the deployment machine into a publisher.

## Mission

Work in `/opt/lab-registry-rights`, on the VMs. The publisher is on `docker.lab`,
the reader on `docker-client.lab`. The registry listens on
`registry-rights.lab.test:15447`, the token service on port `15448`. TLS is
ready. The passwords are in `credentials.json` on `docker.lab`, to be read with
`sudo`. The only thing to repair is `auth.yml`, on `docker.lab`.

### 1. The publisher publishes

The `publisher` account pulls and pushes `catalogue/appli`. Then reload the
`dsoxlab-registry-droits-minimaux-auth` container. The check builds a fresh image
from the supplied `Dockerfile`, pushes it, and expects a digest.

### 2. The reader pulls, and does not publish

From `docker-client.lab`, the `reader` account pulls this digest. The image's
identifier and its output without network are the publisher's. The push of new
content by `reader` is refused for lack of rights, and without the lab's CA, the
pull fails.

### What both checks also require

- `reader` cannot open an upload, even when asking for `pull,push`.
- Neither account reads or writes in another repository.
- Anonymous access and wrong passwords are refused.
- TLS remains verified on both machines: no `insecure-registry`.

For your own tries, keep the credentials in a separate folder, with
`docker --config`, under `/opt/lab-registry-rights`. `dsoxlab clean` puts both
machines back in their previous state.
