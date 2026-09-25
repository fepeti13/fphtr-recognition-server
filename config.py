import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    # Fixed per account (see fphtr-documentations/university-server-connection.md)
    ssh_host: str = os.environ.get("SSH_HOST", "172.30.240.31")
    ssh_port: int = int(os.environ.get("SSH_PORT", "2222"))
    ssh_username: str = os.environ.get("SSH_USERNAME", "md5_s1331aa578af515ae2f53096fac6")
    # Changes every MLHub session - must be supplied fresh, never hardcoded/committed
    ssh_password: str = os.environ.get("SSH_PASSWORD", "")
    models_dir: str = os.environ.get("MODELS_DIR", "~/handwritten-text-recognition-trocr/models")


settings = Settings()
