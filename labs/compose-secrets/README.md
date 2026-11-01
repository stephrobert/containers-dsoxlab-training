# Service-scoped file secrets

Three checks measure the Compose grant, actual read-only mount and observer
denial, metadata/log leakage and consumption after rotation. Tokens are random
pedagogical values, never external credentials. Tests restore the file and consumer.
The supplied image contains no token; cleanup removes only this project's resources.
Standalone file secrets do not claim encrypted storage or protection from host root.
