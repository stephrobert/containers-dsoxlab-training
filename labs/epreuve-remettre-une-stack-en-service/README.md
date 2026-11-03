# Bring a Compose stack back into service

This lab measures a two-service composition: the named project with both its
services up, a front end reaching its data **by service name** on a stack
network, a single façade published on the loopback, data that survives the
stack being recreated, and a configuration where at least one value comes
from an interpolation.

The critical requirement is the **record written before a recreation and
served after it**: it is the one thing a composition loses for good.

## What this lab does not require, and why

Neither a health probe nor a dependency condition. Both are taught in the
next module, and an exam does not grade what the lesson has not introduced.

It does not need them: the supplied front end retries its upstream for a
minute, so start-up order does not matter. That is not a concession, it is
another way of doing without, and it measures just as well.

Run the normal lab cleanup before replaying it. Cleanup removes only
containers, networks, volumes and the image carrying this lab's labels.
