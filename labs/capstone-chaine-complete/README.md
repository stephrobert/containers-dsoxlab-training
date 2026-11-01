# Complete delivery chain

Capstone c4, 180 minutes. Read [the assessment](scenario.md).
Source → multistage BuildKit → actual SPDX inventory → loopback registry →
digest pull → hardened Compose API/PostgreSQL → durable data → eight incidents
→ fresh second-VM restoration → schema-aware release rollback → targeted
maintenance with continuously probed business reads and a restored backup.

Dependencies and exact pins: [provenance](fixtures/PROVENANCE.md). Debian 13
amd64 VMs, Docker/BuildKit, Compose v2 `up --wait`, Python 3, free source
15088/18088 and target 18089. The API also survives dependency interruption
without its container being restarted. Technical tests do not replace human
review of the migration/recovery decision.
Setup alone needs apt/image network access; builds use a bundled hashed wheel.
Only owned containers, images, networks, volumes and `/opt/lab-delivery`
are removed on both VMs; the dedicated target transfer account is removed and
shared bases are preserved. Reference is encrypted in
`solution/capstone-chaine-complete/solution.yaml`.
Pre-pull image IDs distinguish newly seeded bases from preexisting ones;
new bases are removed only if unused and unshared, without force or parent pruning.
