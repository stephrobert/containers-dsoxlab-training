FROM python:3.14.10-slim-trixie@sha256:3cabfd7d7aaf394e6040e79fa1eec6ca1c52b74ed9188650472695d9a9326999
RUN apt-get update && apt-get install -y --no-install-recommends nftables iproute2 iputils-ping && rm -rf /var/lib/apt/lists/*
LABEL dsoxlab.lab="reseau-pare-feu-cible"
COPY service.py /service.py
COPY bootstrap.sh /bootstrap.sh
ENTRYPOINT ["/bin/sh", "/bootstrap.sh"]
