import logging
import threading

import paramiko

from config import settings

logger = logging.getLogger(__name__)

_client: paramiko.SSHClient | None = None
_lock = threading.Lock()


class SSHConnectionError(RuntimeError):
    """Raised when a connection or command to the university server fails."""


def _connect() -> paramiko.SSHClient:
    if not settings.ssh_password:
        raise SSHConnectionError(
            "SSH_PASSWORD is not set. Get the current session password from the MLHub "
            "SSH gateway panel and pass it to the container as SSH_PASSWORD."
        )

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            hostname=settings.ssh_host,
            port=settings.ssh_port,
            username=settings.ssh_username,
            password=settings.ssh_password,
            timeout=10,
        )
    except Exception as exc:
        raise SSHConnectionError(
            f"Could not connect to {settings.ssh_host}:{settings.ssh_port} as {settings.ssh_username}: {exc}"
        ) from exc
    logger.info("Connected to %s:%s", settings.ssh_host, settings.ssh_port)
    return client


def get_client() -> paramiko.SSHClient:
    """Return a live SSH client, connecting lazily on first use and reconnecting after a drop."""
    global _client
    with _lock:
        if _client is not None:
            transport = _client.get_transport()
            if transport is not None and transport.is_active():
                return _client
            _client.close()
        _client = _connect()
        return _client


def run_command(command: str, timeout: int = 30) -> str:
    """Run a command on the university server over the managed SSH connection and return its stdout."""
    client = get_client()
    try:
        _, stdout, stderr = client.exec_command(command, timeout=timeout)
        exit_status = stdout.channel.recv_exit_status()
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
    except Exception as exc:
        # connection may have dropped mid-command - drop the cache so the next call reconnects
        close()
        raise SSHConnectionError(f"SSH command failed: {exc}") from exc

    if exit_status != 0:
        raise SSHConnectionError(f"Remote command exited with status {exit_status}: {err or out}")
    return out


def close() -> None:
    global _client
    with _lock:
        if _client is not None:
            _client.close()
            _client = None
