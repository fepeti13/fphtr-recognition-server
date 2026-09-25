from fastapi import FastAPI

app = FastAPI(title="FPHTR Recognition Server", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "fphtr-recognition-server",
    }


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Recognition server is running."}
