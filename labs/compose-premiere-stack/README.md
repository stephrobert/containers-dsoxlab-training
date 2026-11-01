# A reproducible two-service application

Setup installs Debian's Compose v2 package and builds two tiny services from
pinned Alpine with `busybox-extras`, since the base image does not include the
HTTP server applet. No application containers or Compose declaration exist initially.

Three checks measure the running project and port boundary, live API-to-web
communication through service discovery, and recreation from the declaration.
Containers must have Compose project/service labels, and the recreation check
requires new identities for both containers, not a configuration file alone.

The live-content trial restores the API's original release. Cleanup removes
only the project's labeled containers, networks and volumes, then its
owner-labeled images. It never runs a global prune or removes unrelated projects.
