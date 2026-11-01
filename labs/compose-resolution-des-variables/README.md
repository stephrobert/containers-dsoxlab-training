# Compose interpolation and container environment

Setup supplies a broken declaration, an explicit deployment environment, misleading
implicit defaults and a separate runtime environment. No container exists initially.

Three checks measure the resolved configuration, actual environment and startup
report, then force-recreate with a random shell override. The original deployment
is restored in `finally`. Supplied environment files are checked against setup hashes.
Cleanup removes only this Compose project's labeled resources and its lab files.
The pinned base image is retained; no application image is built.
