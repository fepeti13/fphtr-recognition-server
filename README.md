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

The service opens the SSH connection itself, lazily, the first time an endpoint needs it (see `ssh_client.py`) — nobody has to `ssh` in manually. It reconnects automatically if the connection drops. Configure it with environment variables:

| Variable | Default | Notes |
|---|---|---|
| `SSH_HOST` | `172.30.240.31` | University server address, only reachable over VPN |
| `SSH_PORT` | `2222` | Fixed |
| `SSH_USERNAME` | `md5_s1331aa578af515ae2f53096fac6` | Fixed per account |
| `SSH_PASSWORD` | *(none — required)* | **Changes every MLHub session.** Get it fresh from the SSH gateway panel and pass it to the container each time you spawn a new session. Never commit it. |
| `MODELS_DIR` | `~/handwritten-text-recognition-trocr/models` | Remote directory scanned by `GET /api/v1/models` |

### Reaching the server from Docker (VPN + networking)

The VPN tunnel is a network-namespace construct — WireGuard brought up on the Docker **host** is invisible to a container unless the container shares that network namespace. Decision for now:

- **Bring WireGuard up on the host** (same manual step as before — see the connection doc), then **run this container with host networking**:
  ```bash
  docker run --network host --env-file .env fphtr-recognition-server
  ```
  Linux-only, but simplest and keeps VPN setup exactly as already documented, with no secrets baked into the image.
- Do **not** run WireGuard inside this same container — it would mix concerns and require baking `NET_ADMIN`/privileged capabilities into the app image permanently just to hold a VPN key.
- If host networking stops being viable (e.g. deploying on a host you don't control, or Docker Desktop on macOS/Windows where `--network host` doesn't work), the alternative is a **VPN sidecar container** (its own `wireguard` client, `cap_add: NET_ADMIN`, `/dev/net/tun`, the private `wg0.conf` bind-mounted as a secret — never baked into an image) with this app container joining it via `network_mode: "service:vpn"` in docker-compose. Not implemented yet; revisit if/when this stops running on a single trusted dev machine.
- Either way, spawning the MLHub session itself (browser login, picking a GPU profile) stays a manual human step — it cannot be automated, so `SSH_PASSWORD` still needs to be refreshed per session regardless of the networking approach chosen.

## Status

Early stage — planning and interface contract complete, implementation not yet started. See [`fphtr-documentations`](https://github.com/fepeti13/fphtr-documentations) for the current decisions log and open questions.

## Related

- Docs: [`fphtr-documentations`](https://github.com/fepeti13/fphtr-documentations)
- Jira epic: TM-4 (HTR)
- Interface contract issue: TM-26
- Recognition server issue: TM-29
