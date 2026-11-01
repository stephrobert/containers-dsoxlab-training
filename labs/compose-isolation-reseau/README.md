# Network membership is an observable boundary

Setup builds three HTTP services from pinned Alpine with `busybox-extras`.
Tests inspect actual bridge membership, internal status and port bindings.
A random live-data trial proves the full front-to-API-to-data path.

Isolation is tested with a healthy data server: API access succeeds while front
access fails by DNS name and direct IP. The trial repeats after recreating all
containers, preventing a transient manual network change from passing.
Cleanup removes only project-labeled resources and lab-labeled images.
