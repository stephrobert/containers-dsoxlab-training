# The route exists, but the request does not arrive

## The situation

On `docker.lab`, the project in `/opt/dsoxlab-reseau-pare-feu-cible` contains an
allowed client, an untrusted client, a router and an inventory server. A rule of
the router blocks the business flow.

## Mission

Find the faulty hop and correct only that flow. The other exclusions stay.

1. Use project `dsoxlab-reseau-pare-feu-cible-stack`, directory
   `/opt/dsoxlab-reseau-pare-feu-cible`. Keep both dedicated bridge networks.
   Front: `172.30.201.0/24`, back: `172.30.202.0/24`. Router `.254` on each.
   Allowed client: front `.10`; untrusted client: front `.20`; server: back `.10`.
2. Establish the selected client and return routes via the router. Probe the
   router control service at port 8081, the router-to-server hop and local
   server listeners before concluding that routing or the service is broken.
3. Identify the namespace rule responsible for the business failure. Correct
   only the business path to TCP 8080 and verify the HTTP domain response
   `component: server`, `value: inventory-ready`.
4. Keep default-drop INPUT/FORWARD, established returns, `deny-untrusted`,
   `deny-debug` and `deny-rest` rules. The untrusted client must not reach
   business TCP 8080; allowed client must not reach debug TCP 9090 or mistaken
   TCP 8089. Debug must actually listen on the server, not disappear.
   Fresh denied probes must increment the corresponding drop counters.
5. Recreate the topology from its declaration and repeat permitted and refused
   probes. Do not alter the supplied server or bootstrap code.
6. No workstation/VM firewall or global forwarding change. NET_ADMIN only in
   the containers setting namespace routes; no privileged, host network/PID/IPC,
   host/API socket mounts or published ports. Keep prefixes and lab labels.

Two checks: the flow passes and the exclusions hold, then the same after a
recreation. Removing the whole firewall makes both fail.
