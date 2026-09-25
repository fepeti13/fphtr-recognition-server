from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from config import settings
from ssh_client import SSHConnectionError, run_command

app = FastAPI(title="FPHTR Recognition Server", version="0.1.0")

_loaded_model: str | None = None
_current_image: bytes | None = None
_busy = False


class LoadModelRequest(BaseModel):
    model_name: str


def get_available_models() -> list[str]:
    command = f"find {settings.models_dir} -mindepth 1 -maxdepth 1 -type d -printf '%f\\n' | sort"
    try:
        output = run_command(command)
    except SSHConnectionError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return [line for line in output.splitlines() if line]


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "fphtr-recognition-server",
    }


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Recognition server is running."}


@app.get("/api/v1/models")
def list_models() -> dict[str, list[str]]:
    return {"models": get_available_models()}


@app.post("/api/v1/models/load")
def load_model(request: LoadModelRequest) -> dict[str, str]:
    global _loaded_model, _busy

    if _busy:
        raise HTTPException(status_code=409, detail="A recognition request is already in progress.")

    available_models = get_available_models()
    if request.model_name not in available_models:
        raise HTTPException(status_code=404, detail=f"Model '{request.model_name}' not found.")

    _loaded_model = request.model_name
    return {"status": "loaded", "model_name": request.model_name}


@app.post("/api/v1/image")
async def upload_image(file: UploadFile = File(...)) -> dict[str, str]:
    global _current_image

    if not file:
        raise HTTPException(status_code=400, detail="No file was provided.")

    try:
        image_bytes = await file.read()
    except Exception as exc:  # pragma: no cover - defensive fallback for IO errors
        raise HTTPException(status_code=500, detail=f"Could not read uploaded image: {exc}") from exc

    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    _current_image = image_bytes
    return {"status": "ok"}
