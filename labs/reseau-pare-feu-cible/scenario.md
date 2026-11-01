# The route exists, but the request does not arrive

The dedicated topology in `/opt/dsoxlab-reseau-pare-feu-cible` has an allowed
client, an untrusted client, a router and an inventory service. A real firewall
rule blocks the business flow. Locate the failing hop and correct only that
flow, retaining the untrusted-client and debug-port exclusions.

All firewall commands belong inside the router container's namespace.
Do not alter the workstation or VM firewall, host forwarding, or Docker API.
See [the numbered contract](challenge/README.md) and separate explanation review.
