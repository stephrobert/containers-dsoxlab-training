"""L'API que l'équipe doit livrer en conteneur.

Deux routes : la santé, que l'exploitation interroge, et la version, qui dit
sur quoi l'image a été construite.
"""

from fastapi import FastAPI

app = FastAPI(title="inventaire")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/version")
def version() -> dict[str, str]:
    import platform

    return {"python": platform.python_version()}
