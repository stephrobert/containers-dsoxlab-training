# Readiness differs from liveness

Three checks measure healthy startup, loss of readiness with liveness preserved,
and isolated slow/blocked cold starts. App has no retries or restart policy to hide
a premature start. Trials restore readiness and remove their own projects.
Cleanup removes project-labeled resources and lab-labeled images only.
