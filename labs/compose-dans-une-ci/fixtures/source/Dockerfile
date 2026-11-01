FROM python:3.14.10-alpine3.24@sha256:eb2c62658b8d51bff0acc408504b76521d02030de56a8a3c1e830083e89b89d2
LABEL dsoxlab.lab="compose-dans-une-ci"
ARG SOURCE_COMMIT
LABEL org.opencontainers.image.revision=$SOURCE_COMMIT
WORKDIR /app
COPY . .
CMD ["python", "api.py"]
