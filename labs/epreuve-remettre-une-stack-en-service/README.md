# Compose capstone

This lab checks a complete two-service stack: a successful one-shot writer,
shared named data, service ordering, a read-only web mount, health, and a
loopback-only endpoint. The functional check recreates only web and confirms
the release data remains available.

Run the normal lab cleanup before replaying it. Cleanup removes only containers,
networks, volumes and the image carrying this lab's labels.
