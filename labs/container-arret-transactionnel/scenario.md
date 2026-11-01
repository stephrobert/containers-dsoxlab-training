# A stop that loses an order

The supplied HTTP ledger accepts a write but the deployment interrupts it
during shutdown. The application is already implemented. Repair its launch
and stopping behavior in `/opt/dsoxlab-container-arret-transactionnel`.

Prove signal reception, request completion and durable domain data after
container recreation. Compare an intentionally forced stop of another
in-flight transaction, without damaging earlier committed records.
Run this same service as UID/GID 10001 with a read-only root filesystem.
Only `/data` holds writable application data; another application UID must
be refused access to its transactions. Preserve these restrictions during recovery.

Use only this lab's labelled resources. The numbered contract is in
[challenge/README.md](challenge/README.md); explanation review is separate.
