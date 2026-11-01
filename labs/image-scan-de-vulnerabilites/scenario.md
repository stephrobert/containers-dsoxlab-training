# A scan is dated evidence, not a permanent certificate

On `docker.lab`, work in `/opt/lab-image-scan`. Two scratch **library fixture**
images contain genuine Debian package contents and inventories. They are not
services and must never be executed. `legacy` has OpenSSL 1.1.1n; `fixed` has
OpenSSL 3.0.17. [PROVENANCE.md](fixtures/PROVENANCE.md) documents exact sources
and SHA-256 checksums. The unmodified Debian database is frozen at
2026-11-01 11:37:02 UTC, independent of tomorrow's public-image state.

1. Run `python3 scan.py dsoxlab-scan:legacy legacy-report.json`. Use
   `/usr/bin/python3` if your interpreter lacks system packages. It extracts
   the actual image inventory without starting a container, invokes **debsecan**
   against the offline database and returns 1 for policy rejection.
2. Read the complete findings. The narrowly scoped promotion policy rejects
   **CVE-2023-0286**, the real OpenSSL X.400 type-confusion advisory; it does
   not claim that the corrected image has no other vulnerabilities.
3. Promote the supplied `fixed` image to `dsoxlab-scan:candidate`, scan it to
   `candidate-report.json`, retaining all findings and provenance fields.
4. Create executable `gate.sh IMAGE REPORT` that runs a fresh supplied scan,
   preserves its JSON evidence and returns its status. Prove rejection of
   legacy and acceptance of fixed. Do not filter, edit or fake scanner output.

No success reports, candidate tag or gate exist initially. Checks compare
evidence with freshly executed scanner output, image IDs, inventory and database
hashes. Evidence expires after 24 hours. This is Debian package metadata
scanning, **not** comprehensive language-package or filesystem scanning.
Scratch fixtures deliberately omit package dependencies; they are safe
non-executed library specimens, not deployable applications.

All data and packages are supplied locally; apt installs `debsecan`,
`python3-apt`, Docker and dpkg during setup. Scans/builds then need no network,
scanner container or remote DB update. Fixture packages are amd64; runtime VM
must be amd64. Never publish these specimen images to a public registry.
