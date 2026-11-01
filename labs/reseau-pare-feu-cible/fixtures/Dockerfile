FROM python:3.13.8-slim-bookworm@sha256:61169c2bdb8e6bb44a8dfad33f569d324d52f079fded9a204b322a6fb9c9f799
RUN apt-get update && apt-get install -y --no-install-recommends nftables iproute2 iputils-ping && rm -rf /var/lib/apt/lists/*
LABEL dsoxlab.lab="reseau-pare-feu-cible"
COPY service.py /service.py
COPY bootstrap.sh /bootstrap.sh
ENTRYPOINT ["/bin/sh", "/bootstrap.sh"]
