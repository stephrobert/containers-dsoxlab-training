"""Emit SPDX 2.3 from the running image's actual package inventories."""

import datetime
import hashlib
import importlib.metadata
import json
import subprocess
import sys
from pathlib import Path

image_id = sys.argv[1]
packages = []
for distribution in sorted(importlib.metadata.distributions(), key=lambda d: d.metadata["Name"]):
    name = distribution.metadata["Name"]
    packages.append({
        "name": name, "versionInfo": distribution.version,
        "SPDXID": f"SPDXRef-python-{name.replace('_', '-')}",
        "downloadLocation": "NOASSERTION", "filesAnalyzed": False,
        "licenseConcluded": "NOASSERTION", "licenseDeclared": "NOASSERTION",
        "copyrightText": "NOASSERTION",
    })
for index, line in enumerate(subprocess.check_output(
        ["dpkg-query", "-W", "-f", "${Package}\\t${Version}\\n"], text=True).splitlines()):
    name, version = line.split("\t")
    packages.append({
        "name": name, "versionInfo": version, "SPDXID": f"SPDXRef-debian-{index}",
        "downloadLocation": "NOASSERTION", "filesAnalyzed": False,
        "licenseConcluded": "NOASSERTION", "licenseDeclared": "NOASSERTION",
        "copyrightText": "NOASSERTION",
    })
app_hash = hashlib.sha256(Path("/app/api.py").read_bytes()).hexdigest()
packages.append({
    "name": "delivery-api", "versionInfo": "1.0", "SPDXID": "SPDXRef-api",
    "downloadLocation": "NOASSERTION", "filesAnalyzed": False,
    "licenseConcluded": "NOASSERTION", "licenseDeclared": "NOASSERTION",
    "copyrightText": "NOASSERTION",
    "checksums": [{"algorithm": "SHA256", "checksumValue": app_hash}],
})
print(json.dumps({
    "spdxVersion": "SPDX-2.3", "dataLicense": "CC0-1.0",
    "SPDXID": "SPDXRef-DOCUMENT", "name": "delivery-api",
    "documentNamespace": f"https://dsoxlab.local/spdx/{image_id.replace(':', '/')}",
    "creationInfo": {
        "created": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "creators": ["Tool: dsoxlab-inventory-1.0"],
    },
    "packages": packages,
    "relationships": [
        {"spdxElementId": "SPDXRef-DOCUMENT", "relationshipType": "DESCRIBES",
         "relatedSpdxElement": "SPDXRef-api"},
        *[{"spdxElementId": "SPDXRef-api", "relationshipType": "DEPENDS_ON",
           "relatedSpdxElement": p["SPDXID"]} for p in packages if p["SPDXID"] != "SPDXRef-api"],
    ],
}, indent=2))
