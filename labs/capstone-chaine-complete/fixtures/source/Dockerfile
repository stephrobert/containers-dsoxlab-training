FROM python:3.13.8-slim-bookworm@sha256:61169c2bdb8e6bb44a8dfad33f569d324d52f079fded9a204b322a6fb9c9f799
LABEL dsoxlab.lab="capstone-chaine-complete"
WORKDIR /app
COPY . .
RUN pip install --no-index --find-links=wheels --require-hashes -r requirements.txt
USER 0
CMD ["python", "/app/api.py"]
