# The same Dockerfile no longer finds the same base

## The situation

The `/opt/lab-image-pin/appli` context builds an application on
`127.0.0.1:15004/socle:stable`. The registry moved that tag to a base nobody
approved. The `/opt/lab-image-pin/approbation.json` file gives the reference and
the identity of the approved base.

## Mission

On `docker.lab`, fix `/opt/lab-image-pin/appli/Dockerfile` and build
`dsoxlab-pin:finale` from that context.

### 1. The right delivery

`docker run --rm --network none dsoxlab-pin:finale` prints the identity of the
approved base, then the current source. The image derives from the layers of the
approved base.

### 2. A new source enters the product

The check copies your context, changes `source.txt` and rebuilds. The product
carries the new source and the approved base.

### 3. The base does not follow the tag

The check moves `stable` twice and rebuilds with
`docker build --pull --no-cache`. The base layers remain those of the approved
base. The tag is then put back.

### What is forbidden

Do not change the bases, `approbation.json` or the registry. An old renamed
image or a hardcoded answer does not pass. The registry uses HTTP and listens
only on the loopback.
