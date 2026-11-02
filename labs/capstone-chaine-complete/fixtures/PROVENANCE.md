# Delivery dependencies / Dépendances de livraison

All images are pinned in setup and Dockerfiles. Local builds use only seeded
images and the supplied PyPI wheel; no pip access is needed at build time.

Every digest below is measured against the actual pin in `setup.yaml` and in the
Dockerfiles, not copied from an earlier list: this file ships inside the
delivery, so a stale line here is a false provenance record.

* Python 3.14.10 slim-trixie:
  `sha256:3cabfd7d7aaf394e6040e79fa1eec6ca1c52b74ed9188650472695d9a9326999`.
* PostgreSQL 18.6 alpine3.24:
  `sha256:10a5c69a83035ab5239f5620d708520e8b28f5aa1f2b20143e6024532edadfb5`.
* Distribution registry 3.1.2:
  `sha256:d4032d4cc323c1731c707931ecada07a53076eac38e3b61ae57533f170f2c6c3`.
* psycopg2-binary 2.9.13, CPython 3.14, manylinux2014 amd64:
  https://files.pythonhosted.org/packages/91/ad/7f52f92cc65c23778daff7eec4ee2099236694a0a4723a5f180d0708b607/psycopg2_binary-2.9.13-cp314-cp314-manylinux2014_x86_64.manylinux_2_17_x86_64.whl
  SHA-256 `190c18b97d9ef72f2e88c451b6588af90d6bd7bf54cb94b963280dc86a2c7076`.
  Upstream licence notices are preserved inside the wheel.
  The interpreter tag has to match the base image: a cp313 wheel is refused by
  Python 3.14, so the wheel and `FROM python:` move together.

The SPDX emitter inventories actual installed Debian and Python packages plus
the API source checksum. It is an inventory, not a vulnerability scan.
Build and database tokens are public lab-only credentials, never real secrets.

Les builds utilisent les bases amorcées et la wheel PyPI fournie, sans pip
réseau. Les licences amont sont conservées. Le générateur SPDX relève les
paquets réellement installés et la somme du code API ; ce n'est pas un scan
de vulnérabilités. Les tokens sont publics et réservés au lab.

L'étiquette d'interpréteur de la wheel suit l'image de base : une wheel cp313
est refusée par Python 3.14, donc les deux se changent ensemble.
