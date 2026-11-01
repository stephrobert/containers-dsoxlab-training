# The same Dockerfile no longer finds the same base

On `docker.lab`, `/opt/lab-image-pin/appli` builds an application on
`127.0.0.1:15004/socle:stable`. The registry moved that tag to an unapproved
base. `/opt/lab-image-pin/approbation.json` records the approved base's manifest
digest and identity.

The previous lab recovered a container by digest. Here, a **future rebuild**
must retain the right base while incorporating new application source.

## Mission

- Fix the application Dockerfile to use the approved base.
- Build `dsoxlab-pin:finale` from that context.
- Its container must print the approved base followed by the current source:
  `docker run --rm --network none dsoxlab-pin:finale`.
- Changing the source must change the product without changing its base layers.
- Moving `stable` must not change the base of a forced rebuild using
  `docker build --pull --no-cache`.

Do not change the base images, approval receipt or registry. Reusing an old
final image or printing a hardcoded response does not meet the mission.
The HTTP registry listens only on loopback.

Checks copy your context, change its source, move `stable` twice and rebuild.
They run products without networking and compare layers with the approved
layers. The tag is restored afterwards.
