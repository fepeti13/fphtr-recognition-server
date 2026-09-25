# fphtr-recognition-server

Recognition server for the HTR (handwritten text recognition) pipeline. Loads a fine-tuned TrOCR model and returns predicted text for given regions of an image.

Part of the three-server HTR architecture (UI → segmentation → recognition). Full project context and decisions: [`fphtr-documentations`](https://github.com/fepeti13/fphtr-documentations).

## What this service does

- Exposes a REST API so the UI (eScriptorium) can:
  - list available models,
  - load/unload a model on the GPU,
  - send the current image,
  - request recognition on one or more coordinate regions.
- Runs as a **FastAPI** application in its own **Docker container**.
- Does not run the model itself. It forwards the work over an **SSH connection to the university server (UBB MLHub)**, where a fine-tuned TrOCR model (base/large) is loaded and actually performs recognition.

## Architecture (this repo's place in it)

```
eScriptorium (UI)
   |  REST — see interface contract below
   v
fphtr-recognition-server (this repo, FastAPI, Docker)
   |  SSH
   v
University server (UBB MLHub) — TrOCR model loaded in an SSH session
```

If the SSH connection drops, the loaded model is intentionally dropped too — this avoids a stale model on the university server. The server reloads the model on the next `load` call.

## Interface contract

The UI ↔ recognition server contract (endpoints, request/response schemas, error format) is defined in:

**[`fphtr-documentations/ifc-s/IFC-UI-Recognition.md`](https://github.com/fepeti13/fphtr-documentations)**

Endpoints, v1:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v1/models` | List available model names |
| `POST` | `/api/v1/models/load` | Load a model onto the GPU (replaces any currently loaded model) |
| `POST` | `/api/v1/image` | Set the current image (IIIF URL) |
| `POST` | `/api/v1/recognize` | Recognize one or more coordinate regions of the current image |
| `POST` | `/api/v1/models/unload` | Remove the current model from GPU memory (idempotent) |

v1 status: no auth, single global state (one model, one image, one caller), synchronous calls, no confidence scores. See the interface contract doc for the full list of open questions.

## Connecting to the university server

Details (VPN, SSH, session credentials): [`fphtr-documentations/university-server-connection.md`](https://github.com/fepeti13/fphtr-documentations).

## Status

Early stage — planning and interface contract complete, implementation not yet started. See [`fphtr-documentations`](https://github.com/fepeti13/fphtr-documentations) for the current decisions log and open questions.

## Related

- Docs: [`fphtr-documentations`](https://github.com/fepeti13/fphtr-documentations)
- Jira epic: TM-4 (HTR)
- Interface contract issue: TM-26
- Recognition server issue: TM-29
