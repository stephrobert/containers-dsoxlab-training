# Delivery dependencies / Dépendances de livraison

All images are pinned in setup and Dockerfiles. Local builds use only seeded
images and the supplied PyPI wheel; no pip access is needed at build time.

* Python 3.13.8 slim-bookworm:
  `sha256:61169c2bdb8e6bb44a8dfad33f569d324d52f079fded9a204b322a6fb9c9f799`.
* PostgreSQL 17.6 alpine3.22:
  `sha256:ef257d85f76e48da1c64832459b59fcaba1a4dac97bf5d7450c77753542eee94`.
* Distribution registry 2.8.3:
  `sha256:a3d8aaa63ed8681a604f1dea0aa03f100d5895b6a58ace528858a7b332415373`.
* psycopg2-binary 2.9.11, CPython 3.13, manylinux2014 amd64:
  https://files.pythonhosted.org/packages/3c/7e/6a1a38f86412df101435809f225d57c1a021307dd0689f7a5e7fe83588b1/psycopg2_binary-2.9.11-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.whl
  SHA-256 `5c6ff3335ce08c75afaed19e08699e8aacf95d4a260b495a4a8545244fe2ceb3`.
  Upstream licence notices are preserved inside the wheel.

The SPDX emitter inventories actual installed Debian and Python packages plus
the API source checksum. It is an inventory, not a vulnerability scan.
Build and database tokens are public lab-only credentials, never real secrets.

Les builds utilisent les bases amorcées et la wheel PyPI fournie, sans pip
réseau. Les licences amont sont conservées. Le générateur SPDX relève les
paquets réellement installés et la somme du code API ; ce n'est pas un scan
de vulnérabilités. Les tokens sont publics et réservés au lab.
